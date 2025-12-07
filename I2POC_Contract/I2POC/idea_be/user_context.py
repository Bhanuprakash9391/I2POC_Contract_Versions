from typing import Optional, Dict, Any
from models import DexKoUserContext, DexKoDepartment
import logging

logger = logging.getLogger(__name__)

class UserContextManager:
    """Manages DexKo user context and preferences"""
    
    def __init__(self):
        self.user_profiles = {}  # In production, this would be a database
    
    def create_user_context(self, 
                          user_id: str,
                          department: DexKoDepartment,
                          role: str,
                          location: str = "Unknown",
                          language: str = "en") -> DexKoUserContext:
        """Create a DexKo user context with company-specific information"""
        return DexKoUserContext(
            user_id=user_id,
            department=department,
            role=role,
            location=location,
            language=language
        )
    
    def get_default_user_context(self) -> DexKoUserContext:
        """Get default user context for anonymous users"""
        return DexKoUserContext(
            user_id="anonymous",
            department=DexKoDepartment.OTHER,
            role="Employee",
            location="Unknown",
            language="en"
        )
    
    def get_department_specific_questions(self, department: DexKoDepartment) -> Dict[str, Any]:
        """Get department-specific questions and context"""
        department_contexts = {
            DexKoDepartment.ENGINEERING: {
                "focus_areas": ["Product Design", "Manufacturing Process", "Quality Control"],
                "common_kpis": ["Production Efficiency", "Quality Metrics", "Cost Reduction"],
                "suggested_questions": [
                    "How does this improve engineering processes?",
                    "What manufacturing challenges does this address?",
                    "How does this impact product quality?"
                ]
            },
            DexKoDepartment.MANUFACTURING: {
                "focus_areas": ["Production Line", "Supply Chain", "Operational Efficiency"],
                "common_kpis": ["Throughput", "Downtime Reduction", "Cost per Unit"],
                "suggested_questions": [
                    "How does this optimize manufacturing workflow?",
                    "What supply chain improvements does this enable?",
                    "How does this reduce operational costs?"
                ]
            },
            DexKoDepartment.SALES: {
                "focus_areas": ["Customer Acquisition", "Revenue Growth", "Market Expansion"],
                "common_kpis": ["Sales Conversion", "Customer Retention", "Revenue per Customer"],
                "suggested_questions": [
                    "How does this help acquire new customers?",
                    "What revenue opportunities does this create?",
                    "How does this improve customer relationships?"
                ]
            },
            DexKoDepartment.IT: {
                "focus_areas": ["System Integration", "Data Management", "Security"],
                "common_kpis": ["System Uptime", "Data Accuracy", "Security Compliance"],
                "suggested_questions": [
                    "How does this integrate with existing DexKo systems?",
                    "What data management improvements does this provide?",
                    "How does this enhance security posture?"
                ]
            },
            DexKoDepartment.OPERATIONS: {
                "focus_areas": ["Process Optimization", "Resource Management", "Service Delivery"],
                "common_kpis": ["Process Efficiency", "Resource Utilization", "Service Level"],
                "suggested_questions": [
                    "How does this optimize operational processes?",
                    "What resource efficiencies does this create?",
                    "How does this improve service delivery?"
                ]
            }
        }
        
        return department_contexts.get(department, {
            "focus_areas": ["General Improvement"],
            "common_kpis": ["Cost Savings", "Efficiency Gains"],
            "suggested_questions": [
                "How does this create value for DexKo?",
                "What business problems does this solve?"
            ]
        })
    
    def get_role_specific_context(self, role: str) -> Dict[str, Any]:
        """Get role-specific context and permissions"""
        role_contexts = {
            "Manager": {
                "permissions": ["review_ideas", "evaluate_impact"],
                "focus_areas": ["Team Productivity", "Budget Management", "Strategic Alignment"]
            },
            "Director": {
                "permissions": ["review_ideas", "approve_ideas", "strategic_planning"],
                "focus_areas": ["Business Strategy", "ROI Analysis", "Market Position"]
            },
            "Engineer": {
                "permissions": ["submit_ideas", "technical_implementation"],
                "focus_areas": ["Technical Feasibility", "Implementation Details", "Technical Innovation"]
            },
            "Analyst": {
                "permissions": ["submit_ideas", "data_analysis"],
                "focus_areas": ["Data Insights", "Performance Metrics", "Analytical Approaches"]
            }
        }
        
        return role_contexts.get(role, {
            "permissions": ["submit_ideas"],
            "focus_areas": ["General Improvement"]
        })
    
    def get_language_specific_content(self, language: str) -> Dict[str, str]:
        """Get language-specific content for UI and questions"""
        language_content = {
            "en": {
                "welcome_message": "Welcome to DexKo Idea Platform",
                "idea_intake": "Idea Intake",
                "business_value": "Business Value Analysis",
                "submit_button": "Submit Idea"
            },
            "de": {
                "welcome_message": "Willkommen bei der DexKo Ideenplattform",
                "idea_intake": "Ideenaufnahme",
                "business_value": "Geschäftswertanalyse",
                "submit_button": "Idee einreichen"
            }
        }
        
        return language_content.get(language, language_content["en"])

# Global instance
user_context_manager = UserContextManager()
