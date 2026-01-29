"""
Clinical Rules Engine for CDSS

Implements rule-based clinical safety checks that work alongside
ML predictions for hybrid intelligence decision making.
"""

from dataclasses import dataclass, field
from typing import Dict, List, Optional, Tuple
from enum import Enum
from datetime import datetime
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))
from config import (
    DRUG_INTERACTIONS, VITAL_CRITICAL_RULES, AGE_SAFETY_RULES,
    RULES_ENGINE_CONFIG, EXISTING_CONDITIONS
)


class RuleSeverity(Enum):
    """Severity levels for rule violations."""
    CRITICAL = "critical"   # Requires immediate action
    WARNING = "warning"     # Important but not immediately dangerous
    CAUTION = "caution"     # Worth noting, monitor
    INFO = "info"           # Informational only


@dataclass
class RuleViolation:
    """Represents a clinical rule violation."""
    rule_id: str
    rule_name: str
    severity: RuleSeverity
    message: str
    recommendation: str
    category: str
    data: Dict = field(default_factory=dict)
    
    @property
    def icon(self) -> str:
        icons = {
            RuleSeverity.CRITICAL: "🚨",
            RuleSeverity.WARNING: "⚠️",
            RuleSeverity.CAUTION: "📋",
            RuleSeverity.INFO: "ℹ️"
        }
        return icons.get(self.severity, "📋")
    
    @property
    def color(self) -> str:
        colors = {
            RuleSeverity.CRITICAL: "#dc3545",
            RuleSeverity.WARNING: "#fd7e14",
            RuleSeverity.CAUTION: "#ffc107",
            RuleSeverity.INFO: "#17a2b8"
        }
        return colors.get(self.severity, "#6c757d")


@dataclass
class RulesResult:
    """Result of running all clinical safety rules."""
    violations: List[RuleViolation]
    passed_rules: int
    total_rules: int
    has_critical: bool
    has_warnings: bool
    summary: str
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())
    
    @property
    def pass_rate(self) -> float:
        return self.passed_rules / self.total_rules if self.total_rules > 0 else 1.0
    
    def get_by_severity(self, severity: RuleSeverity) -> List[RuleViolation]:
        return [v for v in self.violations if v.severity == severity]
    
    def get_by_category(self, category: str) -> List[RuleViolation]:
        return [v for v in self.violations if v.category == category]


@dataclass
class HybridDecision:
    """Combined decision from ML and rules engines."""
    ml_risk_level: str
    ml_risk_score: float
    rules_result: RulesResult
    final_risk_level: str
    final_risk_score: float
    decision_rationale: str
    conflicts: List[str]
    recommendations: List[str]


class ClinicalRulesEngine:
    """
    Rule-based clinical safety checks.
    
    Provides deterministic safety rules that complement ML predictions.
    Rules are based on clinical guidelines and best practices.
    """
    
    def __init__(self):
        self.config = RULES_ENGINE_CONFIG
        self.rule_counter = 0
    
    def _generate_rule_id(self, category: str) -> str:
        """Generate unique rule violation ID."""
        self.rule_counter += 1
        return f"{category[:3].upper()}-{self.rule_counter:04d}"
    
    def run_all_checks(self, patient_data: Dict) -> RulesResult:
        """
        Execute all safety rules and return findings.
        
        Args:
            patient_data: Dictionary with patient clinical data
            
        Returns:
            RulesResult with all violations found
        """
        violations = []
        total_rules = 0
        
        categories = self.config.get('rule_categories', {})
        
        # Drug interactions
        if categories.get('drug_interactions', True):
            v, rules = self.check_drug_interactions(patient_data)
            violations.extend(v)
            total_rules += rules
        
        # Vital sign alerts
        if categories.get('vital_sign_alerts', True):
            v, rules = self.check_vital_alerts(patient_data)
            violations.extend(v)
            total_rules += rules
        
        # Age safety
        if categories.get('age_safety', True):
            v, rules = self.check_age_safety(patient_data)
            violations.extend(v)
            total_rules += rules
        
        # Contraindications
        if categories.get('contraindications', True):
            v, rules = self.check_contraindications(patient_data)
            violations.extend(v)
            total_rules += rules
        
        # Allergy checks
        if categories.get('allergy_checks', True):
            v, rules = self.check_allergy_risks(patient_data)
            violations.extend(v)
            total_rules += rules
        
        # Calculate results
        passed = total_rules - len(violations)
        has_critical = any(v.severity == RuleSeverity.CRITICAL for v in violations)
        has_warnings = any(v.severity == RuleSeverity.WARNING for v in violations)
        
        # Generate summary
        if has_critical:
            summary = f"🚨 CRITICAL: {len([v for v in violations if v.severity == RuleSeverity.CRITICAL])} critical safety issue(s) detected!"
        elif has_warnings:
            summary = f"⚠️ WARNING: {len([v for v in violations if v.severity == RuleSeverity.WARNING])} warning(s) require attention"
        elif violations:
            summary = f"📋 {len(violations)} minor issue(s) noted"
        else:
            summary = "✅ All clinical safety checks passed"
        
        return RulesResult(
            violations=violations,
            passed_rules=passed,
            total_rules=total_rules,
            has_critical=has_critical,
            has_warnings=has_warnings,
            summary=summary
        )
    
    def check_drug_interactions(self, patient_data: Dict) -> Tuple[List[RuleViolation], int]:
        """
        Check for known dangerous drug interactions.
        
        Returns:
            Tuple of (violations list, total rules checked)
        """
        violations = []
        medications = patient_data.get('medications', [])
        meds_lower = [m.lower() for m in medications]
        
        # Count total interaction rules
        total_rules = sum(len(v) for v in DRUG_INTERACTIONS.values())
        
        # Check severe interactions
        for interaction in DRUG_INTERACTIONS.get('severe', []):
            drug1, drug2 = interaction['drug1'], interaction['drug2']
            has_drug1 = any(drug1 in m for m in meds_lower)
            has_drug2 = any(drug2 in m for m in meds_lower)
            
            if has_drug1 and has_drug2:
                violations.append(RuleViolation(
                    rule_id=self._generate_rule_id("DRG"),
                    rule_name="Severe Drug Interaction",
                    severity=RuleSeverity.CRITICAL,
                    message=f"SEVERE interaction between {drug1} and {drug2}: {interaction['effect']}",
                    recommendation=f"Review necessity of concurrent {drug1} and {drug2}. Consider alternatives or close monitoring.",
                    category="drug_interactions",
                    data={"drug1": drug1, "drug2": drug2, "effect": interaction['effect']}
                ))
        
        # Check moderate interactions
        for interaction in DRUG_INTERACTIONS.get('moderate', []):
            drug1, drug2 = interaction['drug1'], interaction['drug2']
            has_drug1 = any(drug1 in m for m in meds_lower)
            has_drug2 = any(drug2 in m for m in meds_lower)
            
            if has_drug1 and has_drug2:
                violations.append(RuleViolation(
                    rule_id=self._generate_rule_id("DRG"),
                    rule_name="Moderate Drug Interaction",
                    severity=RuleSeverity.WARNING,
                    message=f"Moderate interaction between {drug1} and {drug2}: {interaction['effect']}",
                    recommendation=f"Monitor for {interaction['effect']}. Consider timing adjustments.",
                    category="drug_interactions",
                    data={"drug1": drug1, "drug2": drug2, "effect": interaction['effect']}
                ))
        
        return violations, total_rules
    
    def check_vital_alerts(self, patient_data: Dict) -> Tuple[List[RuleViolation], int]:
        """
        Check vitals against critical thresholds.
        
        Returns:
            Tuple of (violations list, total rules checked)
        """
        violations = []
        total_rules = len(VITAL_CRITICAL_RULES) * 2  # Low and high for each
        
        for vital_name, thresholds in VITAL_CRITICAL_RULES.items():
            value = patient_data.get(vital_name)
            
            if value is None:
                continue
            
            display_name = vital_name.replace('_', ' ').title()
            
            # Check critical low
            if 'critical_low' in thresholds and value < thresholds['critical_low']:
                violations.append(RuleViolation(
                    rule_id=self._generate_rule_id("VIT"),
                    rule_name=f"Critical Low {display_name}",
                    severity=RuleSeverity.CRITICAL,
                    message=f"CRITICAL: {display_name} is {value}, below critical threshold of {thresholds['critical_low']}",
                    recommendation=f"Immediate assessment required. Verify measurement and initiate appropriate intervention.",
                    category="vital_sign_alerts",
                    data={"vital": vital_name, "value": value, "threshold": thresholds['critical_low'], "type": "low"}
                ))
            
            # Check critical high
            if 'critical_high' in thresholds and value > thresholds['critical_high']:
                violations.append(RuleViolation(
                    rule_id=self._generate_rule_id("VIT"),
                    rule_name=f"Critical High {display_name}",
                    severity=RuleSeverity.CRITICAL,
                    message=f"CRITICAL: {display_name} is {value}, above critical threshold of {thresholds['critical_high']}",
                    recommendation=f"Immediate assessment required. Verify measurement and initiate appropriate intervention.",
                    category="vital_sign_alerts",
                    data={"vital": vital_name, "value": value, "threshold": thresholds['critical_high'], "type": "high"}
                ))
        
        return violations, total_rules
    
    def check_age_safety(self, patient_data: Dict) -> Tuple[List[RuleViolation], int]:
        """
        Age-specific medication safety rules.
        
        Returns:
            Tuple of (violations list, total rules checked)
        """
        violations = []
        age = patient_data.get('age')
        medications = patient_data.get('medications', [])
        
        if age is None or not medications:
            return violations, 0
        
        meds_lower = [m.lower() for m in medications]
        total_rules = 0
        
        # Elderly safety rules
        elderly_rules = AGE_SAFETY_RULES.get('elderly_avoid', {})
        if age >= elderly_rules.get('min_age', 65):
            risky_meds = elderly_rules.get('medications', [])
            total_rules += len(risky_meds)
            
            for risky_med in risky_meds:
                if any(risky_med in m for m in meds_lower):
                    violations.append(RuleViolation(
                        rule_id=self._generate_rule_id("AGE"),
                        rule_name="Elderly Medication Caution",
                        severity=RuleSeverity.WARNING,
                        message=f"Patient age {age}: {risky_med} may be inappropriate for elderly patients",
                        recommendation=elderly_rules.get('reason', 'Consider safer alternatives'),
                        category="age_safety",
                        data={"age": age, "medication": risky_med}
                    ))
        
        # Pediatric safety rules
        pediatric_rules = AGE_SAFETY_RULES.get('pediatric_caution', {})
        if age <= pediatric_rules.get('max_age', 12):
            risky_meds = pediatric_rules.get('medications', [])
            total_rules += len(risky_meds)
            
            for risky_med in risky_meds:
                if any(risky_med in m for m in meds_lower):
                    violations.append(RuleViolation(
                        rule_id=self._generate_rule_id("AGE"),
                        rule_name="Pediatric Medication Caution",
                        severity=RuleSeverity.WARNING,
                        message=f"Patient age {age}: {risky_med} may be inappropriate for pediatric patients",
                        recommendation=pediatric_rules.get('reason', 'Verify pediatric appropriateness'),
                        category="age_safety",
                        data={"age": age, "medication": risky_med}
                    ))
        
        return violations, max(total_rules, 1)
    
    def check_contraindications(self, patient_data: Dict) -> Tuple[List[RuleViolation], int]:
        """
        Check for condition-drug contraindications.
        
        Returns:
            Tuple of (violations list, total rules checked)
        """
        violations = []
        medications = patient_data.get('medications', [])
        meds_lower = [m.lower() for m in medications]
        
        # Define contraindications
        contraindications = [
            {"condition": "kidney_disease", "drugs": ["nsaid", "ibuprofen", "naproxen", "metformin"],
             "reason": "May worsen kidney function or cause toxicity"},
            {"condition": "liver_disease", "drugs": ["acetaminophen", "statin"],
             "reason": "Liver metabolism may be impaired"},
            {"condition": "heart_disease", "drugs": ["nsaid", "ibuprofen"],
             "reason": "May increase cardiovascular risk"},
            {"condition": "asthma", "drugs": ["beta_blocker", "metoprolol", "propranolol", "aspirin"],
             "reason": "May trigger bronchospasm"}
        ]
        
        total_rules = len(contraindications)
        
        for contra in contraindications:
            condition_key = f"condition_{contra['condition']}"
            has_condition = patient_data.get(condition_key, 0) == 1
            
            if has_condition:
                for drug in contra['drugs']:
                    if any(drug in m for m in meds_lower):
                        violations.append(RuleViolation(
                            rule_id=self._generate_rule_id("CON"),
                            rule_name="Drug-Condition Contraindication",
                            severity=RuleSeverity.WARNING,
                            message=f"Caution: {drug} with {contra['condition'].replace('_', ' ')}",
                            recommendation=contra['reason'],
                            category="contraindications",
                            data={"condition": contra['condition'], "drug": drug}
                        ))
        
        return violations, total_rules
    
    def check_allergy_risks(self, patient_data: Dict) -> Tuple[List[RuleViolation], int]:
        """
        Check for allergy-related medication risks.
        
        Returns:
            Tuple of (violations list, total rules checked)
        """
        violations = []
        allergies = patient_data.get('allergies', [])
        medications = patient_data.get('medications', [])
        
        if not allergies or not medications:
            return violations, 1
        
        allergies_lower = [a.lower() for a in allergies]
        meds_lower = [m.lower() for m in medications]
        
        # Cross-reactivity patterns
        cross_reactions = {
            "penicillin": ["amoxicillin", "ampicillin", "cephalosporin"],
            "sulfa": ["sulfamethoxazole", "sulfasalazine"],
            "aspirin": ["nsaid", "ibuprofen", "naproxen"]
        }
        
        total_rules = len(cross_reactions) + len(allergies)
        
        # Direct allergy matches
        for allergy in allergies_lower:
            for med in meds_lower:
                if allergy in med or med in allergy:
                    violations.append(RuleViolation(
                        rule_id=self._generate_rule_id("ALG"),
                        rule_name="Allergy Alert",
                        severity=RuleSeverity.CRITICAL,
                        message=f"ALLERGY ALERT: Patient allergic to {allergy}, prescribed {med}",
                        recommendation="Verify allergy history. Consider alternative medication immediately.",
                        category="allergy_checks",
                        data={"allergy": allergy, "medication": med}
                    ))
        
        # Cross-reactivity checks
        for allergy_class, related_drugs in cross_reactions.items():
            if any(allergy_class in a for a in allergies_lower):
                for drug in related_drugs:
                    if any(drug in m for m in meds_lower):
                        violations.append(RuleViolation(
                            rule_id=self._generate_rule_id("ALG"),
                            rule_name="Cross-Reactivity Risk",
                            severity=RuleSeverity.WARNING,
                            message=f"Cross-reactivity risk: {allergy_class} allergy, prescribed {drug}",
                            recommendation=f"Patient has {allergy_class} allergy. {drug} may cause cross-reaction.",
                            category="allergy_checks",
                            data={"allergy_class": allergy_class, "medication": drug}
                        ))
        
        return violations, total_rules


class HybridDecisionEngine:
    """
    Combines ML predictions with rule-based checks.
    
    Provides a unified decision that leverages both:
    1. ML model's probabilistic predictions
    2. Rule engine's deterministic safety checks
    """
    
    def __init__(self, rules_engine: Optional[ClinicalRulesEngine] = None):
        """
        Initialize the hybrid decision engine.
        
        Args:
            rules_engine: ClinicalRulesEngine instance (created if not provided)
        """
        self.rules_engine = rules_engine or ClinicalRulesEngine()
        self.config = RULES_ENGINE_CONFIG
    
    def make_decision(self, patient_data: Dict,
                      ml_risk_level: str,
                      ml_risk_score: float,
                      ml_probabilities: Optional[Dict] = None) -> HybridDecision:
        """
        Combine ML prediction with rule-based checks.
        
        Args:
            patient_data: Patient clinical data
            ml_risk_level: ML model's predicted risk level
            ml_risk_score: ML model's risk score (0-1)
            ml_probabilities: Optional probability distribution
            
        Returns:
            HybridDecision with combined assessment
        """
        # Run rules engine
        rules_result = self.rules_engine.run_all_checks(patient_data)
        
        # Determine final risk level
        final_level, final_score, rationale, conflicts = self._combine_decisions(
            ml_risk_level, ml_risk_score, rules_result
        )
        
        # Generate combined recommendations
        recommendations = self._generate_recommendations(
            ml_risk_level, rules_result, conflicts
        )
        
        return HybridDecision(
            ml_risk_level=ml_risk_level,
            ml_risk_score=ml_risk_score,
            rules_result=rules_result,
            final_risk_level=final_level,
            final_risk_score=final_score,
            decision_rationale=rationale,
            conflicts=conflicts,
            recommendations=recommendations
        )
    
    def _combine_decisions(self, ml_level: str, ml_score: float,
                           rules_result: RulesResult) -> Tuple[str, float, str, List[str]]:
        """
        Combine ML and rules decisions.
        
        Returns:
            Tuple of (final_level, final_score, rationale, conflicts)
        """
        conflicts = []
        method = self.config.get('combine_method', 'conservative')
        
        # Calculate rules-based risk adjustment
        rules_adjustment = 0.0
        if rules_result.has_critical:
            rules_adjustment = 0.4
        elif rules_result.has_warnings:
            rules_adjustment = 0.2
        elif rules_result.violations:
            rules_adjustment = 0.1
        
        # Detect conflicts
        if ml_level == "Low" and rules_result.has_critical:
            conflicts.append("ML predicts low risk but critical safety violations detected")
        if ml_level == "High" and not rules_result.violations:
            conflicts.append("ML predicts high risk but no rule violations found")
        
        # Combine based on method
        if method == 'conservative':
            # Take the higher risk assessment
            if rules_result.has_critical:
                final_level = "High"
                final_score = max(ml_score, 0.8)
                rationale = "Risk elevated due to critical rule violations"
            elif rules_result.has_warnings and ml_level == "Low":
                final_level = "Medium"
                final_score = max(ml_score + rules_adjustment, 0.4)
                rationale = "Risk elevated due to safety warnings"
            else:
                final_level = ml_level
                final_score = min(ml_score + rules_adjustment, 1.0)
                rationale = "ML prediction with safety rule adjustments"
        
        elif method == 'liberal':
            # Trust ML more, only override for critical
            if rules_result.has_critical:
                final_level = max(ml_level, "High", key=lambda x: {"Low": 0, "Medium": 1, "High": 2}[x])
                final_score = max(ml_score, 0.7)
                rationale = "Risk elevated for critical violations only"
            else:
                final_level = ml_level
                final_score = ml_score
                rationale = "ML prediction (no critical rule violations)"
        
        else:  # 'ml_priority'
            # ML takes priority, rules are advisory
            final_level = ml_level
            final_score = ml_score
            if rules_result.violations:
                rationale = f"ML prediction with {len(rules_result.violations)} advisory findings"
            else:
                rationale = "ML prediction (rules passed)"
        
        return final_level, final_score, rationale, conflicts
    
    def _generate_recommendations(self, ml_level: str,
                                   rules_result: RulesResult,
                                   conflicts: List[str]) -> List[str]:
        """Generate combined recommendations."""
        recommendations = []
        
        # Add recommendations from rule violations
        for violation in rules_result.violations:
            if violation.severity in [RuleSeverity.CRITICAL, RuleSeverity.WARNING]:
                recommendations.append(f"{violation.icon} {violation.recommendation}")
        
        # Add conflict resolution recommendations
        if conflicts:
            recommendations.append("⚖️ Review discrepancy between ML prediction and clinical rules")
        
        # Add level-based recommendations
        if ml_level == "High":
            recommendations.append("🔍 Perform comprehensive clinical review")
        
        # Deduplicate
        return list(dict.fromkeys(recommendations))
    
    def get_decision_visualization_data(self, decision: HybridDecision) -> Dict:
        """
        Prepare data for visualizing the hybrid decision.
        
        Returns:
            Dictionary with visualization data
        """
        violations_by_severity = {
            'critical': len(decision.rules_result.get_by_severity(RuleSeverity.CRITICAL)),
            'warning': len(decision.rules_result.get_by_severity(RuleSeverity.WARNING)),
            'caution': len(decision.rules_result.get_by_severity(RuleSeverity.CAUTION)),
            'info': len(decision.rules_result.get_by_severity(RuleSeverity.INFO))
        }
        
        return {
            'ml_score': decision.ml_risk_score * 100,
            'ml_level': decision.ml_risk_level,
            'final_score': decision.final_risk_score * 100,
            'final_level': decision.final_risk_level,
            'rules_passed': decision.rules_result.passed_rules,
            'rules_total': decision.rules_result.total_rules,
            'rules_pass_rate': decision.rules_result.pass_rate * 100,
            'violations_by_severity': violations_by_severity,
            'has_conflicts': len(decision.conflicts) > 0,
            'rationale': decision.decision_rationale
        }
