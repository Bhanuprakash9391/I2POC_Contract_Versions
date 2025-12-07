export const messagesInitial = [
    {
        role: "assistant",
        content: `Hi! I'm Contract Generation Assistant, ready to help you create comprehensive contract documents.😊
  
   Excited to collaborate! What type of contract would you like to create?💡`,
    },
];

export const sampleRes = {
    session_id: "cab829bb-53cf-40a6-be16-0ea991852008",
    type: "interrupt",
    action: "get_structure_review",
    section: null,
    subsection: null,
    question: null,
    reason: null,
    draft: null,
    idea: "Streamline the research process by implementing advanced data analytics tools to enhance insights, accuracy, and efficiency.",
    title: "Streamlining Research with Advanced Analytics Tools",
    all_sections: [
        {
            section_heading: "Introduction",
            section_purpose: "Provides context and objectives for the Contract.",
            subsections: [
                {
                    subsection_heading: "Purpose",
                    subsection_definition: "Explains the intent and objectives of the Contract.",
                },
                {
                    subsection_heading: "Background",
                    subsection_definition: "Describes the context or history leading to the contract agreement.",
                },
                {
                    subsection_heading: "Goals of the Contract",
                    subsection_definition: "Outlines specific goals the Contract aims to achieve.",
                },
                {
                    subsection_heading: "Scope",
                    subsection_definition: "Defines the boundaries and focus of the Contract.",
                },
            ],
        },
        {
            section_heading: "Parties and Definitions",
            section_purpose: "Identifies the contracting parties and defines key terms used in the contract.",
            subsections: [
                {
                    subsection_heading: "Parties Information",
                    subsection_definition: "Details the legal names and contact information of all parties.",
                },
                {
                    subsection_heading: "Definitions",
                    subsection_definition: "Provides clear definitions for key terms used throughout the contract.",
                },
                {
                    subsection_heading: "Recitals",
                    subsection_definition: "States the background and purpose of the agreement.",
                },
            ],
        },
        {
            section_heading: "Terms and Conditions",
            section_purpose: "Specifies the rights, obligations, and responsibilities of all parties.",
            subsections: [
                {
                    subsection_heading: "Services and Deliverables",
                    subsection_definition: "Details the services to be provided and deliverables expected.",
                },
                {
                    subsection_heading: "Payment Terms",
                    subsection_definition: "Specifies payment amounts, schedules, and methods.",
                },
                {
                    subsection_heading: "Term and Termination",
                    subsection_definition: "Defines the contract duration and termination conditions.",
                },
                {
                    subsection_heading: "Confidentiality",
                    subsection_definition: "Outlines confidentiality obligations and protections.",
                },
            ],
        },
        {
            section_heading: "Legal and Compliance",
            section_purpose: "Defines legal requirements, compliance obligations, and dispute resolution.",
            subsections: [
                {
                    subsection_heading: "Governing Law",
                    subsection_definition: "Specifies the jurisdiction and laws governing the contract.",
                },
                {
                    subsection_heading: "Dispute Resolution",
                    subsection_definition: "Describes the process for resolving disputes.",
                },
                {
                    subsection_heading: "Liability and Indemnification",
                    subsection_definition: "Outlines liability limitations and indemnification clauses.",
                },
                {
                    subsection_heading: "Intellectual Property",
                    subsection_definition: "Defines ownership and usage rights for intellectual property.",
                },
            ],
        },
    ],
    final_state: null,
};
export const sampleDraft = {
    Introduction:
        "This Contract Agreement (the \"Agreement\") is entered into as of [Date] (the \"Effective Date\") by and between [Party A Name], a [Party A Entity Type] with its principal place of business at [Party A Address] (\"Party A\"), and [Party B Name], a [Party B Entity Type] with its principal place of business at [Party B Address] (\"Party B\"). This Agreement sets forth the terms and conditions under which Party A will provide [Services Description] to Party B.\n\nPurpose: The intent of this Agreement is to establish a clear framework for the business relationship between the Parties, ensuring mutual understanding of rights, responsibilities, and expectations. This Agreement aims to facilitate successful collaboration while protecting the legitimate interests of both Parties through clearly defined terms, conditions, and legal protections.",
    "Parties and Definitions":
        "Parties Information: Party A: [Legal Name], [Entity Type], [Address], [Contact Information]. Party B: [Legal Name], [Entity Type], [Address], [Contact Information].\n\nDefinitions: For purposes of this Agreement, the following terms shall have the meanings set forth below: (a) \"Services\" means the services described in Exhibit A attached hereto; (b) \"Deliverables\" means the items to be delivered by Party A to Party B as specified in Exhibit A; (c) \"Confidential Information\" means any non-public information disclosed by one Party to the other that is designated as confidential or that reasonably should be understood to be confidential given the nature of the information and the circumstances of disclosure; (d) \"Term\" means the duration of this Agreement as specified in Section [X].\n\nRecitals: WHEREAS, Party A possesses expertise in [Area of Expertise]; and WHEREAS, Party B desires to engage Party A to provide the Services; and WHEREAS, the Parties wish to set forth the terms and conditions governing their relationship; NOW, THEREFORE, in consideration of the mutual covenants contained herein, the Parties agree as follows:",
    "Terms and Conditions":
        "Services and Deliverables: Party A shall provide the Services described in Exhibit A in a professional and workmanlike manner. All Deliverables shall be delivered in accordance with the schedule set forth in Exhibit A. Party A shall use commercially reasonable efforts to ensure that the Services and Deliverables meet the specifications outlined in this Agreement.\n\nPayment Terms: Party B shall pay Party A the fees set forth in Exhibit B. Invoices shall be submitted monthly and are due within 30 days of receipt. Late payments shall bear interest at the rate of 1.5% per month or the maximum rate allowed by law, whichever is less.\n\nTerm and Termination: This Agreement shall commence on the Effective Date and continue for [Duration] unless terminated earlier in accordance with this Section. Either Party may terminate this Agreement for cause upon 30 days' written notice to the other Party of a material breach, if such breach remains uncured at the expiration of such 30-day period.\n\nConfidentiality: Each Party agrees to hold the other Party's Confidential Information in confidence and not to disclose or use such Confidential Information except as necessary to perform its obligations or exercise its rights under this Agreement. The obligations of confidentiality shall survive termination of this Agreement for a period of [X] years.",
    "Legal and Compliance":
        "Governing Law: This Agreement shall be governed by and construed in accordance with the laws of the State of [State], without regard to its conflict of laws principles.\n\nDispute Resolution: Any dispute arising out of or relating to this Agreement shall be resolved through binding arbitration in [City, State] in accordance with the rules of the American Arbitration Association. The prevailing Party in any arbitration or legal proceeding shall be entitled to recover its reasonable attorneys' fees and costs.\n\nLiability and Indemnification: Party A's total liability under this Agreement shall not exceed the total fees paid by Party B hereunder. Each Party shall indemnify, defend, and hold harmless the other Party from and against any claims, damages, losses, and expenses arising from its breach of this Agreement or negligence.\n\nIntellectual Property: Party A shall retain all right, title, and interest in any pre-existing intellectual property used in providing the Services. Party B shall own all Deliverables created specifically for Party B under this Agreement, subject to Party A's retention of rights to any underlying technology or methodologies.",
};
