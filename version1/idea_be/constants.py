# Idea to Contract Generation Configuration
MAX_QUESTIONS_PER_SECTION = 3  # Reduced for lightweight intake
IDEA_STRUCTURING_NODE = "idea_structuring"
IDEA_STRUCTURING_REVIEW_NODE = "idea_structuring_review"
INITALIZE_STATE_NODE = "initialize_state_node"
SECTION_SELECTOR_NODE = "section_selector_node"
CRITIC_QUESTION_NODE = "critic_question"
USER_INPUT_DRAFT_GENERATOR_NODE = "user_input_draft"
SECTION_REVIEW_NODE = "section_review"

# Contract-specific sections - focused on legal document generation
SECTIONS = [
    {
        "section_heading": "Contract Overview",
        "section_purpose": "Define the basic structure and purpose of the contract",
        "subsections": [
            {"subsection_heading": "Contract Type", "subsection_definition": "What type of contract is being created (lease, service, employment, etc.)?"},
            {"subsection_heading": "Parties Involved", "subsection_definition": "Who are the contracting parties?"},
            {"subsection_heading": "Contract Purpose", "subsection_definition": "What is the main objective of this contract?"},
            {"subsection_heading": "Duration", "subsection_definition": "What is the term or duration of the contract?"}
        ]
    },
    {
        "section_heading": "Terms and Conditions",
        "section_purpose": "Define the specific terms, obligations, and conditions",
        "subsections": [
            {"subsection_heading": "Key Obligations", "subsection_definition": "What are the main responsibilities of each party?"},
            {"subsection_heading": "Payment Terms", "subsection_definition": "What are the payment arrangements and schedules?"},
            {"subsection_heading": "Termination Clauses", "subsection_definition": "Under what conditions can the contract be terminated?"},
            {"subsection_heading": "Dispute Resolution", "subsection_definition": "How will disputes be resolved?"}
        ]
    },
    {
        "section_heading": "Legal Compliance",
        "section_purpose": "Ensure legal requirements and compliance",
        "subsections": [
            {"subsection_heading": "Governing Law", "subsection_definition": "Which jurisdiction's laws govern this contract?"},
            {"subsection_heading": "Regulatory Requirements", "subsection_definition": "What specific regulations must be complied with?"},
            {"subsection_heading": "Liability and Indemnification", "subsection_definition": "What are the liability limitations and indemnification terms?"}
        ]
    }
]

# Final review node
FINAL_REVIEW_NODE = "final_review_node"
