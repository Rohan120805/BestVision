from django.shortcuts import render
from pulp import *
from .models import Child
from django.contrib import messages
from django.shortcuts import redirect
from django.views.generic.edit import CreateView
from django.urls import reverse_lazy
from dataclasses import dataclass
from django.views.decorators.csrf import csrf_protect
from django.utils.decorators import method_decorator

@dataclass
class ResourceInput:
    name: str
    quantity: float
    type: str
    gender_specific: str
    unit: str

@dataclass
class RequirementInput:
    resource_name: str
    quantity_per_child: float
    frequency: str

@csrf_protect
def optimize_resources(request):
    if request.method != 'POST':
        return render(request, 'resource_input.html')

    try:
        # Parse JSON data
        resources_data = json.loads(request.POST.get('resources', '[]'))
        requirements_data = json.loads(request.POST.get('requirements', '[]'))
        
        # Convert input to ResourceInput objects
        resources = [
            ResourceInput(
                name=data['name'],
                quantity=float(data['quantity']),
                type=data['type'],
                gender_specific=data['gender_specific'],
                unit=data['unit']
            ) for data in resources_data
        ]

        # Convert input to RequirementInput objects
        requirements = [
            RequirementInput(
                resource_name=data['resource_name'],
                quantity_per_child=float(data['quantity_per_child']),
                frequency=data['frequency']
            ) for data in requirements_data
        ]

        # Create optimization model
        model = LpProblem("Orphanage_Resource_Allocation", LpMinimize)
        
        # Get children from database
        children = Child.objects.all()
        
        # Separate integral and divisible resources
        integral_types = ['CLOTHING', 'EDUCATION']
        
        # Decision variables
        allocations = {}
        
        # Create variables and add constraints
        for r in resources:
            total_allocated = 0
            for c in children:
                if r.gender_specific != 'ALL' and c.gender != r.gender_specific:
                    continue
                    
                if r.type in integral_types:
                    allocations[c.id, r.name] = LpVariable(
                        f"allocation_{c.id}_{r.name}", 
                        lowBound=0,
                        cat='Integer'
                    )
                else:
                    allocations[c.id, r.name] = LpVariable(
                        f"allocation_{c.id}_{r.name}", 
                        lowBound=0
                    )
                total_allocated += allocations[c.id, r.name]
            
            # Add constraint: total allocation cannot exceed available quantity
            model += total_allocated <= r.quantity, f"Max_{r.name}"

        # Add requirement constraints
        for req in requirements:
            for c in children:
                matching_resource = next((r for r in resources if r.name == req.resource_name), None)
                if matching_resource:
                    if matching_resource.gender_specific != 'ALL' and c.gender != matching_resource.gender_specific:
                        continue
                    model += allocations[c.id, req.resource_name] >= req.quantity_per_child, f"Min_{c.id}_{req.resource_name}"

        # Objective: Minimize total allocation
        model += lpSum(
            allocations[c.id, r.name]
            for c in children
            for r in resources
            if (c.id, r.name) in allocations
        )

        # Solve the model
        model.solve()

        if model.status == 1:  # Optimal solution found
            allocation_results = []
            
            # Calculate allocation results
            for child in children:
                for resource in resources:
                    if resource.gender_specific != 'ALL' and child.gender != resource.gender_specific:
                        continue
                    
                    if (child.id, resource.name) in allocations:
                        allocation_value = value(allocations[child.id, resource.name])
                        if allocation_value > 0:
                            if resource.type in integral_types:
                                allocation_value = round(allocation_value)
                            
                            allocation_results.append({
                                'child': child,
                                'resource_name': resource.name,
                                'quantity': allocation_value,
                                'unit': resource.unit
                            })

            return render(request, 'allocation_results.html', {
                'allocations': allocation_results
            })
        else:
            messages.error(request, "Could not find optimal solution!")
            return redirect('resource_input')
            
    except Exception as e:
        messages.error(request, f"Error during optimization: {str(e)}")
        return render(request, 'resource_input.html')


class ChildCreateView(CreateView):
    model = Child
    fields = ['name', 'age', 'gender', 'admission_date']
    template_name = 'child_form.html'
    success_url = reverse_lazy('home')

    def form_valid(self, form):
        messages.success(self.request, 'Child added successfully!')
        return super().form_valid(form)

def home(request):
    context = {
        'children': Child.objects.all()
    }
    return render(request, 'home.html', context)

def resource_input(request):
    return render(request, 'resource_input.html')

