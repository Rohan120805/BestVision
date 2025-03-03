from django.shortcuts import get_object_or_404, render
from pulp import *
from .models import Child, Resource, Requirement, Allocation
from django.contrib import messages
from django.shortcuts import redirect
from django.views.generic.edit import CreateView, UpdateView
from django.urls import reverse_lazy

def optimize_resources(request):
    # Create optimization model
    model = LpProblem("Orphanage_Resource_Allocation", LpMinimize)
    
    # Get all data
    children = Child.objects.all()
    resources = Resource.objects.all()
    requirements = Requirement.objects.all()
    
    # Get unique resource types
    resource_types = list(resources.values_list('type', flat=True).distinct())
    
    # Separate integral and divisible resources
    integral_types = ['CLOTHING', 'EDUCATION']
    
    # Decision variables with appropriate bounds
    allocations = {}
    valid_combinations = []  # Track valid child-resource combinations
    
    for c in children:
        for r in resources:
            if r.gender_specific != 'ALL' and c.gender != r.gender_specific:
                continue
                
            valid_combinations.append((c.id, r.id))
            if r.type in integral_types:
                allocations[c.id, r.id] = LpVariable(
                    f"allocation_{c.id}_{r.id}", 
                    lowBound=0, 
                    cat='Integer'
                )
            else:
                allocations[c.id, r.id] = LpVariable(
                    f"allocation_{c.id}_{r.id}", 
                    lowBound=0
                )
    
    # Fairness variables
    min_allocations = LpVariable.dicts("min_allocation",
                                     resource_types,
                                     lowBound=0)
    
    # Objective function - only include valid combinations
    model += lpSum(allocations[c.id, r.id] * float(r.cost_per_unit) 
                   for c in children for r in resources 
                   if (c.id, r.id) in valid_combinations)
    
    # Resource availability constraints - only include valid combinations
    for resource in resources:
        model += lpSum(allocations[c.id, resource.id] 
                      for c in children 
                      if (c.id, resource.id) in valid_combinations) <= float(resource.quantity)
            
    # Fairness constraints with type-specific handling
    for resource in resources:
        for child in children:
            # Skip if gender-specific resource doesn't match child's gender
            if (child.id, resource.id) not in valid_combinations:
                continue
                
            # Base fairness constraint
            model += allocations[child.id, resource.id] >= min_allocations[resource.type]
            
            # Fairness between children
            for other_child in children:
                # Skip comparisons with invalid combinations
                if (other_child.id, resource.id) not in valid_combinations:
                    continue
                    
                if child != other_child:
                    if resource.type in integral_types:
                        # For integral resources, allow difference of at most 1 unit
                        model += allocations[child.id, resource.id] <= allocations[other_child.id, resource.id] + 1
                        model += allocations[child.id, resource.id] >= allocations[other_child.id, resource.id] - 1
                    else:
                        # For divisible resources, keep 20% tolerance
                        model += allocations[child.id, resource.id] <= 1.2 * allocations[other_child.id, resource.id]
                        model += allocations[child.id, resource.id] >= 0.8 * allocations[other_child.id, resource.id]
    
    # Minimum requirements constraints
    for requirement in requirements:
        total_available = float(requirement.resource.quantity)
        min_per_child = total_available / len(children)
        
        for child in children:
            if (child.id, requirement.resource.id) not in valid_combinations:
                continue
                
            if requirement.resource.type in integral_types:
                # For integral resources, round down the minimum requirement
                model += allocations[child.id, requirement.resource.id] >= int(min(requirement.quantity_per_child, min_per_child))
            else:
                # For divisible resources, use exact values
                model += allocations[child.id, requirement.resource.id] >= min(requirement.quantity_per_child, min_per_child)
    
    # Solve the model
    model.solve()
    
    if model.status == 1:  # Optimal solution found
        Allocation.objects.all().delete()
        remaining_resources = {}
        daily_requirements = {}
        
        # Calculate daily requirements per resource type
        for requirement in requirements:
            if requirement.frequency == 'DAILY':
                resource = requirement.resource
                daily_requirements[resource.id] = requirement.quantity_per_child * len(children)
        
        for child in children:
            for resource in resources:
                if resource.gender_specific != 'ALL' and child.gender != resource.gender_specific:
                    continue

                allocation_value = value(allocations[child.id, resource.id])
                if allocation_value > 0:
                    if resource.type in integral_types:
                        allocation_value = round(allocation_value)
                    
                    # Create allocation
                    Allocation.objects.create(
                        child=child,
                        resource=resource,
                        quantity=allocation_value
                    )
                    
                    # Track remaining resources
                    if resource.id not in remaining_resources:
                        remaining_resources[resource.id] = float(resource.quantity)
                    remaining_resources[resource.id] -= allocation_value
        
        # Calculate days of food remaining
        days_of_food = {}
        for resource in resources:
            if resource.type == 'FOOD' and resource.id in remaining_resources and resource.id in daily_requirements:
                remaining = remaining_resources[resource.id]
                daily_need = daily_requirements[resource.id]
                days = int(remaining / daily_need) if daily_need > 0 else 0
                days_of_food[resource.name] = {
                    'remaining': remaining,
                    'daily_need': daily_need,
                    'days': days
                }
        
        messages.success(request, "Resources allocated fairly and successfully!")
        
        # Add information about remaining resources
        for resource_name, info in days_of_food.items():
            messages.info(
                request,
                f"{resource_name}: {info['remaining']:.2f} units remaining. "
                f"With daily requirement of {info['daily_need']:.2f} units, "
                f"sufficient for {info['days']} days."
            )
    else:
        messages.error(request, "Could not find optimal solution!")
    
    return redirect('allocation_list')

def allocation_list(request):
    allocations = Allocation.objects.all().order_by('-date_allocated')
    return render(request, 'allocation_list.html', {'allocations': allocations})

class ChildCreateView(CreateView):
    model = Child
    fields = ['name', 'age', 'admission_date']
    template_name = 'child_form.html'
    success_url = reverse_lazy('home')

    def form_valid(self, form):
        messages.success(self.request, 'Child added successfully!')
        return super().form_valid(form)

def update_donation(request, pk):
    resource = get_object_or_404(Resource, pk=pk)
    if request.method == 'POST':
        quantity = float(request.POST.get('quantity', 0))
        resource.quantity += quantity
        resource.save()
        messages.success(request, f'Added {quantity} {resource.unit} of {resource.name}')
        return redirect('home')
    return render(request, 'donation_form.html', {'resource': resource})

def home(request):
    context = {
        'children': Child.objects.all(),
        'resources': Resource.objects.all(),
        'allocations': Allocation.objects.all().order_by('-date_allocated')[:10],
        'requirements': Requirement.objects.all()
    }
    return render(request, 'home.html', context)