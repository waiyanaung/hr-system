from fastapi import FastAPI, HTTPException
from motor.motor_asyncio import AsyncIOMotorClient
from pydantic import BaseModel, EmailStr
from bson import ObjectId
from typing import Optional
import os

app = FastAPI(title="HR Management API", version="1.0.0")

# --- Database connection ---
MONGO_URL = os.getenv("MONGO_URL", "mongodb://localhost:27017")
client = AsyncIOMotorClient(MONGO_URL)
db = client.hr_db

# --- Pydantic models ---
class EmployeeCreate(BaseModel):
    name: str
    email: str
    department: str
    position: str
    salary: float

class LeaveRequest(BaseModel):
    employee_id: str
    leave_type: str        # annual, medical, unpaid
    start_date: str
    end_date: str
    reason: Optional[str] = None

# --- Health check ---
@app.get("/health")
async def health():
    return {"status": "ok", "service": "fastapi"}

# ── Employees ──────────────────────────────────────

@app.get("/employees")
async def list_employees():
    employees = []
    async for emp in db.employees.find():
        emp["_id"] = str(emp["_id"])
        employees.append(emp)
    return employees

@app.post("/employees", status_code=201)
async def create_employee(emp: EmployeeCreate):
    # Check duplicate email
    existing = await db.employees.find_one({"email": emp.email})
    if existing:
        raise HTTPException(status_code=400, detail="Email already exists")
    result = await db.employees.insert_one(emp.model_dump())
    return {"id": str(result.inserted_id), "message": "Employee created"}

@app.get("/employees/{emp_id}")
async def get_employee(emp_id: str):
    try:
        emp = await db.employees.find_one({"_id": ObjectId(emp_id)})
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid ID format")
    if not emp:
        raise HTTPException(status_code=404, detail="Employee not found")
    emp["_id"] = str(emp["_id"])
    return emp

@app.put("/employees/{emp_id}")
async def update_employee(emp_id: str, emp: EmployeeCreate):
    try:
        result = await db.employees.update_one(
            {"_id": ObjectId(emp_id)},
            {"$set": emp.model_dump()}
        )
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid ID format")
    if result.matched_count == 0:
        raise HTTPException(status_code=404, detail="Employee not found")
    return {"message": "Employee updated"}

@app.delete("/employees/{emp_id}")
async def delete_employee(emp_id: str):
    try:
        result = await db.employees.delete_one({"_id": ObjectId(emp_id)})
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid ID format")
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Employee not found")
    return {"message": "Employee deleted"}

# ── Leave Requests ──────────────────────────────────

@app.get("/leaves")
async def list_leaves():
    leaves = []
    async for leave in db.leaves.find():
        leave["_id"] = str(leave["_id"])
        leaves.append(leave)
    return leaves

@app.post("/leaves", status_code=201)
async def create_leave(leave: LeaveRequest):
    data = leave.model_dump()
    data["status"] = "pending"
    result = await db.leaves.insert_one(data)
    return {"id": str(result.inserted_id), "message": "Leave request submitted"}

@app.put("/leaves/{leave_id}/approve")
async def approve_leave(leave_id: str):
    try:
        await db.leaves.update_one(
            {"_id": ObjectId(leave_id)},
            {"$set": {"status": "approved"}}
        )
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid ID format")
    return {"message": "Leave approved"}

# ── Departments ─────────────────────────────────────

@app.get("/departments")
async def list_departments():
    pipeline = [
        {"$group": {"_id": "$department", "count": {"$sum": 1}}},
        {"$sort": {"_id": 1}}
    ]
    departments = []
    async for dept in db.employees.aggregate(pipeline):
        departments.append({"name": dept["_id"], "headcount": dept["count"]})
    return departments