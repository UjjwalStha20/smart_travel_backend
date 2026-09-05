# Mermaid Class Diagram Analysis

**Source**: All files in `app/` directory (models, schemas, core, services, routers)

**Total Classes**: 17 SQLModel tables
**Total Enums**: 9 enums

## Diagram

```mermaid
classDiagram
    class User {
        +id: UUID
        +name: str
        +role: UserRole
        +nationality: str|null
        +email: EmailStr
        +phone: str|null
        +created_at: datetime
        +updated_at: datetime
    }
    class UserRole {
        <<enumeration>>
        +traveler: "traveler"
        +guide: "guide"
        +admin: "admin"
    }
    class PaceType {
        <<enumeration>>
        +slow: "slow"
        +normal: "normal"
        +fast: "fast"
    }
    class BudgetType {
        <<enumeration>>
        +budget: "budget"
        +standard: "standard"
        +luxury: "luxury"
    }
    class TripStatus {
        <<enumeration>>
        +planned: "planned"
        +ongoing: "ongoing"
        +completed: "completed"
    }
    class UserTrip {
        +id: UUID
        +user_id: UUID
        +destination_id: UUID
        +route_id: UUID
        +pace_type: PaceType
        +budget_type: BudgetType
        +start_date: date|null
        +end_date: date|null
        +status: TripStatus
    }
    class Itinerary {
        +id: UUID
        +trip_id: UUID
        +day_number: int
        +start_location: str
        +end_location: str
        +overnight_location: str|null
        +estimated_walking_hours: Decimal|null
        +notes: str|null
    }
    class SavedDestination {
        +id: UUID
        +user_id: UUID
        +destination_id: UUID
        +created_at: datetime
    }
    class DestinationCategory {
        <<enumeration>>
        +attraction: "attraction"
        +trek: "trek"
    }
    class Destination {
        +id: UUID
        +name: str
        +category: DestinationCategory
        +description: str
        +best_time: list
        +permit_required: bool
        +rating: int|null
        +created_at: datetime
        +address_id: UUID
    }
    class Address {
        +id: UUID
        +province: str|null
        +district: str|null
        +place: str|null
        +latitude: float|null
        +longitude: float|null
        +altitude: float|null
    }
    class TrekkingRoute {
        +id: UUID
        +destination_id: UUID
        +route_name: str
        +difficulty: Difficulty
        +total_distance_km: Decimal|null
        +recommended_days: int|null
        +max_altitude: int|null
        +description: str|null
    }
    class Difficulty {
        <<enumeration>>
        +easy: "easy"
        +moderate: "moderate"
        +hard: "hard"
    }
    class RoutePoint {
        +id: UUID
        +route_id: UUID
        +sequence_no: int
        +name: str
        +distance_from_previous_km: Decimal|null
        +walking_hours_from_previous: Decimal|null
        +overnight_stop: bool
        +description: str|null
        +address_id: UUID
        +accommodation_id: UUID|null
        +food_cost_id: UUID|null
    }
    class Accommodation {
        +id: UUID
        +budget_price: Decimal
        +standard_price: Decimal|null
        +luxury_price: Decimal|null
    }
    class FoodCost {
        +id: UUID
        +budget_price: Decimal
        +standard_price: Decimal|null
        +luxury_price: Decimal|null
    }
    class AttractionType {
        <<enumeration>>
        +temple: "temple"
        +heritage: "heritage"
        +hiking: "hiking"
        +lake: "lake"
        +viewpoint: "viewpoint"
    }
    class Attraction {
        +id: UUID
        +destination_id: UUID
        +attraction_types: list
        +opening_hours: str|null
        +visit_duration_hours: Decimal|null
    }
    class EntryCategory {
        <<enumeration>>
        +nepali: "Nepali"
        +saarc: "SAARC"
        +foreign: "Foreign"
    }
    class EntryFee {
        +id: UUID
        +attraction_id: UUID
        +category: EntryCategory
        +price: Decimal
    }
    class PermitCategory {
        <<enumeration>>
        +nepali: "Nepali"
        +saarc: "SAARC"
        +foreign: "Foreign"
    }
    class Permit {
        +id: UUID
        +destination_id: UUID
        +category: PermitCategory
        +price: Decimal
    }
    class Blog {
        +id: UUID
        +title: str
        +slug: str
        +content: str
        +excerpt: str|null
        +author_id: UUID|null
        +featured_image: str|null
        +category: str|null
        +tags: list|null
        +is_published: bool
        +published_at: datetime|null
        +created_at: datetime
        +updated_at: datetime
    }
    class ChatConversation {
        +id: UUID
        +user_id: UUID
        +title: str
        +created_at: datetime
        +updated_at: datetime
    }
    class ChatMessage {
        +id: UUID
        +conversation_id: UUID
        +role: str
        +content: str
        +created_at: datetime
    }
    class DestinationItinerary {
        +id: UUID
        +destination_id: UUID
        +day_number: int
        +title: str|null
        +start_location: str
        +end_location: str
        +overnight_location: str|null
        +estimated_walking_hours: Decimal|null
        +notes: str|null
    }
    class ActivityLog {
        +id: UUID
        +user_id: UUID
        +user_name: str
        +action: str
        +target: str
        +type: str
        +created_at: datetime
    }
    
    User ||--o{ UserTrip : trips
    User ||--o{ Photo : photos
    User ||--o{ Review : reviews
    User ||--o{ ChatConversation : chat_conversations
    User ||--o{ Blog : blogs
    
    UserTrip ||--o{ User : user
    UserTrip ||--o{ Destination : destination
    UserTrip ||--o{ TrekkingRoute : route
    UserTrip ||--o{ Itinerary : itineraries
    
    SavedDestination ||--o{ User : user
    SavedDestination ||--o{ Destination : destination
    
    Destination ||--o{ UserTrip : user_trips
    Destination ||--o{ TrekkingRoute : trekking_routes
    Destination ||--o{ Permit : permits
    Destination ||--o{ Photo : photos
    Destination ||--o{ Review : reviews
    Destination ||--o{ SavedDestination : saved_destinations
    Destination ||--o{ DestinationItinerary : destination_itineraries
    
    TrekkingRoute ||--o{ RoutePoint : route_points
    
    Address ||--o{ RoutePoint : route_points
    Address ||--o{ Destination : destinations
    
    RoutePoint ||--o{ Accommodation : accommodation
    RoutePoint ||--o{ FoodCost : food_cost
    RoutePoint ||--o{ Address : address
    
    Attraction ||--o{ EntryFee : entry_fees
    
    Blog ||--o{ User : author
    
    ChatConversation ||--o{ ChatMessage : messages
    
    DestinationItinerary ||--o{ Destination : destination
    
    ActivityLog ||--o{ User : user_id (FK)
```

## Detected Structure

**Classes**: 17
- User, UserTrip, Itinerary, SavedDestination
- Destination, Address, TrekkingRoute, RoutePoint
- Accommodation, FoodCost, Attraction, EntryFee
- Blog, ChatConversation, ChatMessage, DestinationItinerary
- ActivityLog

**Enums**: 9
- UserRole (traveler, guide, admin)
- PaceType (slow, normal, fast)
- BudgetType (budget, standard, luxury)
- TripStatus (planned, ongoing, completed)
- DestinationCategory (attraction, trek)
- Difficulty (easy, moderate, hard)
- EntryCategory (Nepali, SAARC, Foreign)
- PermitCategory (Nepali, SAARC, Foreign)
- AttractionType (temple, heritage, hiking, lake, viewpoint)

**Main Relationships** (using `||--o{` Mermaid convention where `||`=1 and `o{`=0-or-many):

1. **User** → **UserTrip** (trips): User has many UserTrips
2. **User** → **Photo** (photos): User has many photos
3. **User** → **Review** (reviews): User has many reviews
4. **User** → **ChatConversation** (chat_conversations): User has many chat conversations
5. **User** → **Blog** (blogs): User has many blogs
6. **UserTrip** → **User** (user): Each UserTrip belongs to one User
7. **UserTrip** → **Destination** (destination): Each UserTrip has one Destination
8. **UserTrip** → **TrekkingRoute** (route): Each UserTrip has one TrekkingRoute
9. **UserTrip** → **Itinerary** (itineraries): Each UserTrip has one Itinerary
10. **SavedDestination** → **User** (user): Each SavedDestination belongs to one User
11. **SavedDestination** → **Destination** (destination): Each SavedDestination references one Destination
12. **Destination** → **UserTrip** (user_trips): Destination has many UserTrips
13. **Destination** → **TrekkingRoute** (trekking_routes): Destination has many TrekkingRoutes
14. **Destination** → **Permit** (permits): Destination has many Permits
15. **Destination** → **Photo** (photos): Destination has many photos
16. **Destination** → **Review** (reviews): Destination has many reviews
17. **Destination** → **SavedDestination** (saved_destinations): Destination has many SavedDestinations
18. **Destination** → **DestinationItinerary** (destination_itineraries): Destination has many DestinationItineraries
19. **TrekkingRoute** → **RoutePoint** (route_points): TrekkingRoute has many RoutePoints
20. **Address** → **RoutePoint** (route_points): Address has many RoutePoints
21. **Address** → **Destination** (destinations): Address has many Destinations
22. **RoutePoint** → **Accommodation** (accommodation): Each RoutePoint optionally has one Accommodation
23. **RoutePoint** → **FoodCost** (food_cost): Each RoutePoint optionally has one FoodCost
24. **RoutePoint** → **Address** (address): Each RoutePoint has one Address (required FK)
25. **Attraction** → **EntryFee** (entry_fees): Attraction has many EntryFees
26. **Blog** → **User** (author): Each Blog optionally has one User author
27. **ChatConversation** → **ChatMessage** (messages): ChatConversation has many ChatMessages
28. **DestinationItinerary** → **Destination** (destination): Each DestinationItinerary has one Destination
29. **ActivityLog** → **User** (user_id): ActivityLog optionally references one User via FK

**Uncertain/Missing Relationships**:

1. **AttractionType enum**: Defined in `attraction_model.py` and imported in `models/__init__.py`, but the `Attraction` class uses `attraction_types: Optional[list]` (just a JSON list) rather than a typed `AttractionType` field. The enum exists in source code but is not directly related to the Attraction class structure.

2. **ActivityLog Relationship**: The `ActivityLog` model defines `user_id: Optional[UUID] = Field(default=None, foreign_key="users.id")` but uses SQLModel `Field()` rather than `Relationship()`, so it's a foreign key constraint rather than an explicit SQLModel Relationship. The diagram shows it as an `||--o{` relationship, but it's technically a FK-only association.

3. **RoutePoint optional FKs**: `RoutePoint.accommodation_id` and `RoutePoint.food_cost_id` are `Optional[UUID]` fields, meaning a RoutePoint may have zero or one associated Accommodation/FoodCost. The `||--o{` notation indicates "0 or many" at the right end, which loosely captures this, but the exact cardinality is "0 or 1" rather than "0 or many".

4. **Blog.author optional**: `Blog.author: Optional["User"] = Relationship(back_populates="blogs")` means a Blog may have no author. The `||--o{` notation at the User end captures this "zero or one" aspect.

5. **No explicit many-to-many relationships**: All relationships in the codebase are one-to-one or one-to-many, as defined by the SQLModel Relationship() definitions. There are no many-to-many junction tables.

6. **ChatMessage.conversation_id FK**: The `ChatMessage` model has `conversation_id: UUID = Field(foreign_key="chat_conversation.id", ondelete="CASCADE")` which is a required FK, and the `ChatConversation.messages: List["ChatMessage"]` relationship is properly captured in the diagram.

---
*Diagram generated by analyzing all source files in the `app/` directory. The Mermaid code is at `backend/mermaid_diagram.mmd` and can be copy-pasted into https://mermaid.live/ for rendering.*