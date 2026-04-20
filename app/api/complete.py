from fastapi import APIRouter, HTTPException
from app.models.complete import CompleteRequest
from app.core.redis import get_redis
from app.core.database import get_db

router = APIRouter()

@router.post("/truck/move/complete", status_code=200)
def complete_move(request: CompleteRequest):
    conn   = get_db()
    r      = get_redis()
    cursor = conn.cursor()

    try:
        # fetch the assignment
        cursor.execute("""
            SELECT id, customer_id, driver_id, assigned_truck, status
            FROM move_assignments
            WHERE id = %s
        """, (request.assignment_id,))

        row = cursor.fetchone()

        if not row:
            raise HTTPException(
                status_code=404,
                detail=f"Assignment {request.assignment_id} not found"
            )

        assignment_id, customer_id, driver_id, assigned_truck, current_status = row

        if current_status == "COMPLETED":
            raise HTTPException(
                status_code=400,
                detail=f"Assignment {assignment_id} is already completed"
            )

        if current_status == "PENDING":
            raise HTTPException(
                status_code=400,
                detail=f"Assignment {assignment_id} was never assigned so it cannot be completed"
            )

        if assigned_truck != request.truck_id:
            raise HTTPException(
                status_code=400,
                detail=f"Truck {request.truck_id} is not assigned to assignment {assignment_id}"
            )

        # update Postgres
        cursor.execute("""
            UPDATE move_assignments
            SET status = 'COMPLETED'
            WHERE id = %s
        """, (assignment_id,))

        truck_data = r.hgetall(request.truck_id)

        if not truck_data:
            print(f"Warning: truck {request.truck_id} not found in Redis, skipping reset")
        else:
            r.hset(request.truck_id, mapping={
                "status":    "available",
                "driver_id": truck_data.get(b"driver_id", b"").decode(),
                "type":      truck_data.get(b"type", b"").decode(),
            })

        conn.commit()

        return {
            "status":        "completed",
            "assignment_id": assignment_id,
            "truck_id":      request.truck_id,
            "customer_id":   customer_id,
            "driver_id":     driver_id,
            "message":       f"Move completed. Truck {request.truck_id} is now available."
        }

    except HTTPException:
        conn.rollback()
        raise
    except Exception as e:
        conn.rollback()
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        cursor.close()
        conn.close()