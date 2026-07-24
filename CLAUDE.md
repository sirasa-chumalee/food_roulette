# CLAUDE.md - Project Specification & AI Architecture Blueprint
## Project: Food Roulette AI Assistant

### 1. Project Overview & Objective
An Android-focused mobile application where users interact with an advanced AI Agent to get hyper-personalized, real-time restaurant recommendations. The core value proposition transitions the traditional random "Food Roulette" into an intelligent, context-aware decision engine that respects strict health, religious, and lifestyle constraints while dynamically adapting to user moods and conversational context.

### 2. Tech Stack & Architecture Assumptions
*   **Frontend / Client:** Flutter & Dart (Target: Android OS).
*   **Backend & Orchestration:** 
    *   *Authentication & User Management:* Secure Login system (OAuth2/Firebase Auth or Custom JWT backend).
    *   *AI Agent Flow:* Python-based backend (e.g., FastAPI, LangGraph/LangChain) is highly assumed for execution, exposing REST/WebSocket APIs to the Flutter client. (Direct execution of advanced RAG/Agentic workflows natively in Dart is discouraged due to ecosystem limitations).
*   **Database & Vector Store:** Relational/NoSQL database for user profiles and transaction history + Vector Database (e.g., Pinecone, PGVector, Qdrant) for Restaurant RAG/Knowledge Base.

---

### 3. Comprehensive User Preference Data Model
To achieve flawless, real-time filtering and recommendation, the AI requires a structured data model split into **Hard Constraints** (Non-negotiable safety/religious rules) and **Soft Preferences** (Dynamic, mood-based, or style choices).

#### A. Hard Constraints (Deterministic Filtering - Safety & Beliefs)
*   **Food Allergies (Medical Urgency):**
    *   *Data Types:* Enumerated List / Bitmask flags.
    *   *Common Inputs:* Peanuts, Tree Nuts, Shellfish, Fish, Wheat/Gluten, Soy, Milk, Eggs, Sesame.
    *   *AI Requirement:* Must act as a strict `PRE_FILTER` or `POST_FILTER` in the database query. The AI must *never* have the autonomy to override this via semantic reasoning to avoid health hazards.
*   **Religious Restrictions (Halal, Kosher, etc.):**
    *   *Data Types:* Strict category flags.
    *   *Common Inputs:* Halal, Kosher, Vegetarian (strict religious variants like Jainism - no root vegetables).
    *   *AI Requirement:* Strict metadata filtering within the Vector/Relational Database.
*   **Severe Dietary Intolerances:**
    *   *Common Inputs:* Celiac Disease (Strict Gluten-Free), Severe Lactose Intolerance.

#### B. Soft Preferences (Probabilistic Filtering - Taste & Lifestyle)
*   **Dietary Style / Regimes:**
    *   *Inputs:* Keto, Low-Carb, Vegan, Vegetarian (Lacto-Ovo), Mediterranean, Carnivore.
*   **Taste Profile Preferences:**
    *   *Inputs:* Spicy tolerance (None, Mild, Medium, Extreme), Sweet vs. Savory bias, Texture preferences.
*   **Price Tier Boundaries:**
    *   *Inputs:* Budget ($), Moderate ($$), Premium ($$$), Luxury ($$$$).
*   **Operational & Environmental Preferences (As seen in UI Mockup):**
    *   *Inputs:* Parking availability, Child-friendly, Pet-friendly, Outdoor seating, Air Conditioning, Noise levels.

#### C. Contextual & Real-time Variables (Injected at Runtime)
*   **Current Geolocation:** Latitude and Longitude coordinates to compute distance radii.
*   **Timestamp Data:** Time of day (Breakfast, Lunch, Dinner, Late Night) and day of the week to cross-reference with restaurant opening hours.
*   **Current Mood / Craving (Extracted from Chat):** e.g., "I'm feeling a bit greasy, want to eat greens" -> Maps to a shift toward low-fat, high-fiber/salad categories.

---

### 4. AI Agent & RAG Workflow Specification
The architecture must prevent the LLM from hallucinating non-existent restaurants or violating hard constraints.

```
[User Input / Chat] 
       │
       ▼
[Intent Parsing & Entity Extraction Agent] ──(Extracts Mood, Parking needs, Cravings)
       │
       ├──────────────────────────────┐
       ▼                              ▼
[Relational DB Lookup]        [Vector DB Retrieval]
(Fetches Hard Constraints)    (Semantic Search on Restaurant KB)
(Allergies, Religion, Loc)    (Embeddings matching Cravings)
       │                              │
       └──────────────┬───────────────┘
                      ▼
            [Deterministic Hybrid Filter] (Applies Hard Exclusion Rules)
                      │
                      ▼
            [RAG Prompt Construction] (Context: Filtered Restaurants + User Profile)
                      │
                      ▼
            [LLM Orchestrator / LangGraph] 
                      │
                      ▼
[Structured JSON Output] ──(Returns UI Metadata to Flutter Client)
```

1.  **Intent Parsing:** Extract entities from the conversation (e.g., "craving seafood" -> Food Type: Seafood; "unless there's parking tho" -> Facility Constraint: Parking=True).
2.  **Hybrid Retrieval:** Query the Vector Store using the semantic embedding of the craving, but strictly apply metadata filters using the user's **Hard Constraints** and real-time geographic radius.
3.  **Generation & Structuring:** The Agent formats the top valid recommendations into a clean JSON array matching the Flutter UI components (Name, Rating, Category, Image URL, Coordinates).

---

### 5. Interaction Logging & Feedback Loop (History Module)
Every user action within the recommended card stack must trigger an event to build an implicit feedback loop.

*   **Data Points to Log per Action:**
    *   `Session_ID`: To group single conversational threads.
    *   `User_ID`: Reference to the active account.
    *   `Restaurant_ID`: The unique identifier of the recommended venue.
    *   `Action_Type`: `IMPRESSION` (shown), `CLICK` (opened details), `ROULETTE_SPIN` (selected via random action), `REJECTION` (swiped away/ignored).
    *   `Timestamp`: Microsecond accuracy for sequential order tracking.
    *   `Conversational_Context`: A snapshot of the text prompt that led to this recommendation.
*   **Utilization of History:**
    *   **Short-term:** Prevent the AI from recommending the exact same restaurant multiple times in a single chat session if the user explicitly rejected it.
    *   **Long-term:** Feed into an embedding adjustment or collaborative filtering layer to refine the "Soft Preferences" score over time.

---

# INSTRUCTIONS FOR CLAUDE DESIGN PHASE

Dear Claude, 

Please review the specification above and design the following concrete implementation details for this Food Roulette application:

1.  **Database Schema Design:** Provide a production-ready SQL/NoSQL schema covering `Users`, `User_Preferences` (handling the hard/soft split), `Restaurants_Metadata` (structured for easy vector-filtering), and `User_Action_History`.
2.  **API Design (Flutter to Backend):** Define the REST/WebSocket endpoints required for authentication, sending a chat message, receiving structured recommendations, and logging history actions.
3.  **RAG Guardrail Strategy:** Detail how you will guarantee 100% compliance with `Food Allergies` and `Religious Restrictions` without letting the LLM's stochastic nature cause dangerous errors.
4.  **State Management Framework Strategy:** Suggest the best state management approach in Flutter (e.g., Bloc, Riverpod) to handle a continuous chat feed that seamlessly embeds dynamically updating interactive restaurant cards.