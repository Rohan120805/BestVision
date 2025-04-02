from django.shortcuts import render
from pulp import *
from .models import Child
from django.contrib import messages
from django.shortcuts import redirect
from django.views.generic.edit import CreateView
from django.urls import reverse_lazy
from dataclasses import dataclass
from django.views.decorators.csrf import csrf_protect
from datetime import datetime, timedelta

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
        resources_data = json.loads(request.POST.get('resources', '[]'))
        requirements_data = json.loads(request.POST.get('requirements', '[]'))
        
        resources = [
            ResourceInput(
                name=data['name'],
                quantity=float(data['quantity']),
                type=data['type'],
                gender_specific=data['gender_specific'].upper(),  
                unit=data['unit']
            ) for data in resources_data
        ]

        requirements = [
            RequirementInput(
                resource_name=data['resource_name'],
                quantity_per_child=float(data['quantity_per_child']),
                frequency=data['frequency']
            ) for data in requirements_data
        ]

        model = LpProblem("Orphanage_Resource_Allocation", LpMinimize)
        children = Child.objects.all()
        integral_types = ['CLOTHING', 'EDUCATION']
        allocations = {}

        # Create variables for valid child-resource pairs
        for resource in resources:
            total_allocated = 0
            for child in children:
                child_gender = child.gender.upper()
                resource_gender = resource.gender_specific.upper()
                
                # Only create variables for valid gender combinations
                if resource_gender == 'ALL' or child_gender == resource_gender:
                    var_name = f"allocation_{child.id}_{resource.name}"
                    if resource.type in integral_types:
                        allocations[(child.id, resource.name)] = LpVariable(
                            var_name, 
                            lowBound=0,
                            cat='Integer'
                        )
                    else:
                        allocations[(child.id, resource.name)] = LpVariable(
                            var_name, 
                            lowBound=0
                        )
                    total_allocated += allocations[(child.id, resource.name)]
            
            # Add resource quantity constraint
            if total_allocated != 0:  # Only add constraint if variables were created
                model += total_allocated <= resource.quantity, f"Max_{resource.name}"

        # Add requirements constraints
        for req in requirements:
            matching_resource = next((r for r in resources if r.name == req.resource_name), None)
            if matching_resource:
                for child in children:
                    child_gender = child.gender.upper()
                    resource_gender = matching_resource.gender_specific.upper()
                    
                    if resource_gender == 'ALL' or child_gender == resource_gender:
                        key = (child.id, req.resource_name)
                        if key in allocations:
                            model += allocations[key] >= req.quantity_per_child, f"Min_{child.id}_{req.resource_name}"

        # Objective function - minimize total allocation
        model += lpSum(
            allocations[key] for key in allocations.keys()
        )

        # Solve the model
        status = model.solve()

        if status == 1:  # Optimal solution found
            allocation_results = []
            resource_exhaustion = {}
            resource_totals = {r.name: 0 for r in resources}  # Initialize all resource totals
            
            # Process allocations
            for (child_id, resource_name), var in allocations.items():
                allocation_value = value(var)
                if allocation_value > 0:
                    child = next(c for c in children if c.id == child_id)
                    resource = next(r for r in resources if r.name == resource_name)
                    
                    if resource.type in integral_types:
                        allocation_value = round(allocation_value)
                    
                    resource_totals[resource_name] += allocation_value
                    
                    allocation_results.append({
                        'child': child,
                        'resource_name': resource_name,
                        'quantity': allocation_value,
                        'unit': resource.unit
                    })
            
            # Calculate resource exhaustion
            for resource in resources:
                total_allocated = resource_totals.get(resource.name, 0)
                if total_allocated > 0:
                    requirement = next(
                        (req for req in requirements if req.resource_name == resource.name),
                        None
                    )
                    
                    if requirement:
                        if requirement.frequency == 'DAILY':
                            daily_usage = total_allocated
                        elif requirement.frequency == 'WEEKLY':
                            daily_usage = total_allocated / 7
                        else:
                            daily_usage = total_allocated / 30
                        
                        days_left = int(resource.quantity / daily_usage)
                        exhaustion_date = datetime.now() + timedelta(days=days_left)
                        
                        resource_exhaustion[resource.name] = {
                            'days_left': days_left,
                            'exhaustion_date': exhaustion_date.strftime('%Y-%m-%d'),
                            'daily_usage': daily_usage,
                            'unit': resource.unit
                        }

            return render(request, 'allocation_results.html', {
                'allocations': allocation_results,
                'resource_exhaustion': resource_exhaustion,
                'resources': resources,
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