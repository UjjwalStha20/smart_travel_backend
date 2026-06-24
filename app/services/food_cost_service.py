from fastapi import HTTPException
from sqlmodel import select
from app.models import FoodCost


class FoodCostService:
    def __init__(self, session):
        self.session = session
    
    def get_all_food_costs(self, offset: int = 0, limit: int = 100):
        foods = select(FoodCost).offset(offset).limit(limit)
        return self.session.exec(foods).all()
    
    def get_food_cost_by_id(self, food_id):
        food = self.session.get(FoodCost, food_id)
        if not food:
            raise HTTPException(status_code=404, detail="Food cost not found")
        return food
    
    def create_food_cost(self, food_data: FoodCost):
        food = FoodCost(**food_data.model_dump())
        self.session.add(food)
        self.session.commit()
        self.session.refresh(food)
        return food
    
    def update_food_cost(self, food_id, food_data: FoodCost):
        existing_food = self.get_food_cost_by_id(food_id)
        if not existing_food:
            raise HTTPException(status_code=404, detail="Food cost not found")
        patch = food_data.model_dump(exclude_unset=True)
        for key, value in patch.items():
            setattr(existing_food, key, value)
        self.session.add(existing_food)
        self.session.commit()
        self.session.refresh(existing_food)
        return existing_food
    
    def delete_food_cost(self, food_id):
        food = self.get_food_cost_by_id(food_id)
        self.session.delete(food)
        self.session.commit()
        return {"message": "Food cost deleted successfully."}