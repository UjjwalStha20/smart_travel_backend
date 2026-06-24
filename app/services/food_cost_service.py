from fastapi import HTTPException
from sqlmodel import select
from app.models import FoodCost
from app.schemas import FoodCostCreate


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
        statement = select(FoodCost).where(
            FoodCost.budget_price == food_data.budget_price,
            FoodCost.standard_price == food_data.standard_price,
            FoodCost.luxury_price == food_data.luxury_price
        )
        existing_food = self.session.exec(statement).first()
        print(food_data)
        if existing_food:
            return existing_food
        else:
            food = FoodCost(**food_data.model_dump())
            self.session.add(food)
            self.session.commit()
            self.session.refresh(food)
            return food
    
    def update_food_cost(self, food_id, food_data: FoodCost):
        statement = select(FoodCost).where(
            FoodCost.budget_price == food_data.budget_price,
            FoodCost.standard_price == food_data.standard_price,
            FoodCost.luxury_price == food_data.luxury_price,
            FoodCost.id != food_id
        )
        existing_food = self.session.exec(statement).first()
        if existing_food:
            self.delete_food_cost(food_id)
            self.session.refresh(existing_food)
            return existing_food
        else:
            existing_food = self.get_food_cost_by_id(food_id)
            patch = food_data.model_dump(exclude_unset=True)
            existing_food.sqlmodel_update(patch)
            self.session.commit()
            self.session.refresh(existing_food)
            return existing_food
    
    def delete_food_cost(self, food_id):
        food = self.get_food_cost_by_id(food_id)
        self.session.delete(food)
        self.session.commit()
        return {"message": "Food cost deleted successfully."}