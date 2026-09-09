from .user_model import User ,UserTrip, Itinerary, SavedDestination
from .destination_model import Destination, DestinationCategory
from .address_model import Address
from .photo_model import Photo
from .review_model import Review
from .attraction_model import Attraction, AttractionType
from .permit_model import Permit
from .trekking_route_model import TrekkingRoute
from .route_point_model import RoutePoint
from .food_cost_model import FoodCost
from .accomodation_model import Accommodation
from .entry_fee_model import EntryFee, EntryCategory
from .blog_model import Blog
from .chat_model import ChatConversation, ChatMessage
from .destination_itinerary_model import DestinationItinerary
from .destination_content_model import DestinationHighlight, DestinationThingToDo, DestinationFaq
from .activity_log_model import ActivityLog
from .user_preference_model import UserPreferences
from .user_interaction_model import UserInteraction
from .recommendation_log_model import RecommendationLog
from .destination_type_detail_model import (
    AccommodationType,
    TrekDetails,
    HikeDetails,
    MountainDetails,
    NatureDetails,
)
from .trip_plan_model import (
    TripPlan,
    TripPlanStatus,
    TripPreference,
    TripItineraryDay,
    TripItineraryItem,
    TripConversation,
    TripMessage,
    TripEdit,
    TripRecommendation,
)
