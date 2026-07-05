from django.shortcuts import render

# Create your views here.
import requests
from django.shortcuts import render, redirect
from django.conf import settings
from django.contrib import messages

API = settings.FASTAPI_URL

def dashboard(request):
    try:
        employees = requests.get(f"{API}/employees", timeout=5).json()
        departments = requests.get(f"{API}/departments", timeout=5).json()
        leaves = requests.get(f"{API}/leaves", timeout=5).json()
    except Exception:
        employees, departments, leaves = [], [], []
    for emp in employees:
        emp["id"] = emp.pop("_id")
    return render(request, "dashboard.html", {
        "employees": employees,
        "departments": departments,
        "leaves": leaves,
        "total_employees": len(employees),
        "pending_leaves": sum(1 for l in leaves if l.get("status") == "pending"),
    })

def create_employee(request):
    if request.method == "POST":
        payload = {
            "name": request.POST["name"],
            "email": request.POST["email"],
            "department": request.POST["department"],
            "position": request.POST["position"],
            "salary": float(request.POST["salary"]),
        }
        resp = requests.post(f"{API}/employees", json=payload, timeout=5)
        if resp.status_code == 201:
            messages.success(request, "Employee created successfully.")
        else:
            messages.error(request, resp.json().get("detail", "Error"))
        return redirect("dashboard")
    return render(request, "create_employee.html")

def delete_employee(request, emp_id):
    requests.delete(f"{API}/employees/{emp_id}", timeout=5)
    messages.success(request, "Employee deleted.")
    return redirect("dashboard")