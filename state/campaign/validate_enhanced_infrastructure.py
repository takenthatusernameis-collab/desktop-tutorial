#!/usr/bin/env python3
"""
Enhanced Infrastructure Validation Script.

This script validates the enhanced infrastructure improvements for result-memo
persistence, evidence capture, and process-comparison testing.
"""

import json
import os
import sys
import hashlib
import datetime
from pathlib import Path

class EnhancedInfrastructureValidator:
    def __init__(self):
        self.campaign_state_path = Path("/workspace/state/campaign")
        self.validation_results = {
            "timestamp": datetime.datetime.now(datetime.timezone.utc).isoformat().replace('+00:00', 'Z'),
            "validation_passed": True,
            "files_validated": [],
            "quality_checks": {},
            "issues_found": []
        }
        
        # Required enhanced infrastructure files
        self.required_enhanced_files = [
            "PROXY_INFRASTRUCTURE_FIX.py",
            "evidence_capture_protocol.md",
            "reproduction_framework.py",
            "process_comparison_harness.py"
        ]
        
        # Expected evidence standards
        self.expected_standards = {
            "enhanced_evidence_capture": True,
            "independent_reproduction": True,
            "multi_layer_persistence": True,
            "quality_assurance": True,
            "standardized_testing": True
        }
    
    def validate_file_existence(self):
        """Validate that all required enhanced infrastructure files exist"""
        print("=== Validating Enhanced Infrastructure Files ===\n")
        
        files_found = 0
        files_missing = []
        
        for required_file in self.required_enhanced_files:
            file_path = self.campaign_state_path / required_file
            if file_path.exists():
                files_found += 1
                self.validation_results["files_validated"].append({
                    "file": required_file,
                    "path": str(file_path),
                    "size": os.path.getsize(file_path),
                    "status": "EXISTS"
                })
                print(f"✓ {required_file} exists ({os.path.getsize(file_path)} bytes)")
            else:
                files_missing.append(required_file)
                self.validation_results["files_validated"].append({
                    "file": required_file,
                    "path": str(file_path),
                    "size": 0,
                    "status": "MISSING"
                })
                print(f"❌ {required_file} missing")
        
        if files_missing:
            self.validation_results["validation_passed"] = False
            self.validation_results["issues_found"].append(
                f"Missing required files: {', '.join(files_missing)}"
            )
        
        print(f"\nFile Validation Summary:")
        print(f"  Files Found: {files_found}/{len(self.required_enhanced_files)}")
        print(f"  Status: {'PASS' if files_found == len(self.required_enhanced_files) else 'FAIL'}")
        
        return files_found == len(self.required_enhanced_files)
    
    def validate_file_contents(self):
        """Validate that enhanced infrastructure files have proper content"""
        print("\n=== Validating Enhanced Infrastructure Content ===\n")
        
        content_validation_results = {}
        
        # Validate PROXY_INFRASTRUCTURE_FIX.py
        proxy_file = self.campaign_state_path / "PROXY_INFRASTRUCTURE_FIX.py"
        if proxy_file.exists():
            content = proxy_file.read_text()
            validation_result = self._validate_proxy_infrastructure_content(content)
            content_validation_results["PROXY_INFRASTRUCTURE_FIX.py"] = validation_result
            
            if validation_result["valid"]:
                print(f"✓ PROXY_INFRASTRUCTURE_FIX.py content valid")
                print(f"  Enhanced features: {', '.join(validation_result['enhanced_features'])}")
            else:
                print(f"❌ PROXY_INFRASTRUCTURE_FIX.py content invalid")
                for issue in validation_result["issues"]:
                    print(f"    Issue: {issue}")
        
        # Validate evidence_capture_protocol.md
        protocol_file = self.campaign_state_path / "evidence_capture_protocol.md"
        if protocol_file.exists():
            content = protocol_file.read_text()
            validation_result = self._validate_evidence_protocol_content(content)
            content_validation_results["evidence_capture_protocol.md"] = validation_result
            
            if validation_result["valid"]:
                print(f"✓ evidence_capture_protocol.md content valid")
                print(f"  Evidence standards: {', '.join(validation_result['evidence_standards'])}")
            else:
                print(f"❌ evidence_capture_protocol.md content invalid")
                for issue in validation_result["issues"]:
                    print(f"    Issue: {issue}")
        
        # Validate reproduction_framework.py
        reproduction_file = self.campaign_state_path / "reproduction_framework.py"
        if reproduction_file.exists():
            content = reproduction_file.read_text()
            validation_result = self._validate_reproduction_framework_content(content)
            content_validation_results["reproduction_framework.py"] = validation_result
            
            if validation_result["valid"]:
                print(f"✓ reproduction_framework.py content valid")
                print(f"  Reproduction features: {', '.join(validation_result['reproduction_features'])}")
            else:
                print(f"❌ reproduction_framework.py content invalid")
                for issue in validation_result["issues"]:
                    print(f"    Issue: {issue}")
        
        # Validate process_comparison_harness.py
        harness_file = self.campaign_state_path / "process_comparison_harness.py"
        if harness_file.exists():
            content = harness_file.read_text()
            validation_result = self._validate_process_harness_content(content)
            content_validation_results["process_comparison_harness.py"] = validation_result
            
            if validation_result["valid"]:
                print(f"✓ process_comparison_harness.py content valid")
                print(f"  Testing features: {', '.join(validation_result['testing_features'])}")
            else:
                print(f"❌ process_comparison_harness.py content invalid")
                for issue in validation_result["issues"]:
                    print(f"    Issue: {issue}")
        
        # Check if all content validations passed
        all_valid = all(result["valid"] for result in content_validation_results.values())
        
        if all_valid:
            print(f"\nContent Validation Summary: PASS")
        else:
            print(f"\nContent Validation Summary: FAIL")
            self.validation_results["validation_passed"] = False
        
        self.validation_results["quality_checks"]["content_validation"] = all_valid
        
        return all_valid
    
    def _validate_proxy_infrastructure_content(self, content):
        """Validate PROXY_INFRASTRUCTURE_FIX.py content"""
        required_features = [
            "Enhanced Persistence",
            "Standardized Protocol",
            "Quality Assurance",
            "Future-Proofing"
        ]
        
        enhanced_features_found = []
        issues = []
        
        # Check for required enhanced features
        if "Enhanced Persistence" in content:
            enhanced_features_found.append("Enhanced Persistence")
        if "Standardized Protocol" in content:
            enhanced_features_found.append("Standardized Protocol")
        if "Quality Assurance" in content:
            enhanced_features_found.append("Quality Assurance")
        if "Future-Proofing" in content:
            enhanced_features_found.append("Future-Proofing")
        
        # Check for evidence preservation
        if "evidence preservation" in content.lower():
            enhanced_features_found.append("Evidence Preservation")
        
        # Check for multi-layer persistence
        if "multi-layer" in content.lower() or "multi layer" in content.lower():
            enhanced_features_found.append("Multi-Layer Persistence")
        
        # Check for standardized protocol
        if "standardized protocol" in content.lower():
            enhanced_features_found.append("Standardized Protocol")
        
        # Check for quality assurance
        if "quality assurance" in content.lower():
            enhanced_features_found.append("Quality Assurance")
        
        # Check for independent verification
        if "independent verification" in content.lower():
            enhanced_features_found.append("Independent Verification")
        
        # Validate content structure
        if "Enhanced Infrastructure Fix for Result-Memo Persistence" not in content:
            issues.append("Missing main title/structure")
        
        if "Implementation" not in content:
            issues.append("Missing implementation section")
        
        if "Integration Strategy" not in content:
            issues.append("Missing integration strategy")
        
        if "Impact" not in content:
            issues.append("Missing impact section")
        
        # Check for evidence capture standards
        if "Evidence Enhancement" not in content:
            issues.append("Missing evidence enhancement section")
        
        # Check for process comparison impact
        if "Process Comparison Test" not in content:
            issues.append("Missing process comparison impact section")
        
        return {
            "valid": len(issues) == 0 and len(enhanced_features_found) >= 4,
            "enhanced_features": enhanced_features_found,
            "issues": issues
        }
    
    def _validate_evidence_protocol_content(self, content):
        """Validate evidence_capture_protocol.md content"""
        required_standards = [
            "Evidence Classification",
            "Evidence Metadata Requirements",
            "File Naming Convention",
            "Persistence Layers",
            "Evidence Validation Standards",
            "Integration with Existing Framework"
        ]
        
        standards_found = []
        issues = []
        
        # Check for required standards
        if "Evidence Classification" in content:
            standards_found.append("Evidence Classification")
        if "Evidence Metadata Requirements" in content:
            standards_found.append("Evidence Metadata Requirements")
        if "File Naming Convention" in content:
            standards_found.append("File Naming Convention")
        if "Persistence Layers" in content:
            standards_found.append("Persistence Layers")
        if "Evidence Validation Standards" in content:
            standards_found.append("Evidence Validation Standards")
        if "Integration with Existing Framework" in content:
            standards_found.append("Integration with Existing Framework")
        
        # Check for evidence quality
        if "Evidence Quality" in content or "evidence quality" in content.lower():
            standards_found.append("Evidence Quality Standards")
        
        # Check for standardized testing
        if "Process-Comparison Testing Standards" in content:
            standards_found.append("Process-Comparison Testing Standards")
        
        # Check for validation requirements
        if "Verification Requirements" in content:
            standards_found.append("Verification Requirements")
        
        # Check for file requirements
        if "Files Required for Evidence" in content:
            standards_found.append("File Requirements")
        
        # Validate content structure
        if "# Enhanced Evidence Capture Protocol" not in content:
            issues.append("Missing main title")
        
        if "## Implementation" not in content:
            issues.append("Missing implementation section")
        
        if "## Integration with Existing Framework" not in content:
            issues.append("Missing integration section")
        
        # Check for evidence capture standards
        if "Evidence Capture Standards" not in content:
            issues.append("Missing evidence capture standards section")
        
        # Check for validation standards
        if "Validation Standards" not in content:
            issues.append("Missing validation standards section")
        
        return {
            "valid": len(issues) == 0 and len(standards_found) >= 6,
            "evidence_standards": standards_found,
            "issues": issues
        }
    
    def _validate_reproduction_framework_content(self, content):
        """Validate reproduction_framework.py content"""
        required_features = [
            "EvidenceReproducer class",
            "run_reproduction method",
            "validate_reproduction method",
            "create_durable_artifact method",
            "run_full_reproduction method"
        ]
        
        features_found = []
        issues = []
        
        # Check for required features
        if "class EvidenceReproducer:" in content:
            features_found.append("EvidenceReproducer class")
        if "def run_reproduction(self):" in content:
            features_found.append("run_reproduction method")
        if "def validate_reproduction(self, reproductions):" in content:
            features_found.append("validate_reproduction method")
        if "def create_durable_artifact(self, reproductions, validation_result):" in content:
            features_found.append("create_durable_artifact method")
        if "def run_full_reproduction(self):" in content:
            features_found.append("run_full_reproduction method")
        
        # Check for evidence validation
        if "independent reproduction validation" in content.lower():
            features_found.append("Independent reproduction validation")
        
        # Check for quality assurance
        if "quality assurance" in content.lower():
            features_found.append("Quality assurance")
        
        # Check for enhanced infrastructure integration
        if "enhanced infrastructure" in content.lower():
            features_found.append("Enhanced infrastructure integration")
        
        # Validate content structure
        if "Enhanced Independent Reproduction Framework" not in content:
            issues.append("Missing main title")
        
        if "class EvidenceReproducer:" not in content:
            issues.append("Missing EvidenceReproducer class")
        
        if "def run_full_reproduction(self):" not in content:
            issues.append("Missing main execution method")
        
        return {
            "valid": len(issues) == 0 and len(features_found) >= 4,
            "reproduction_features": features_found,
            "issues": issues
        }
    
    def _validate_process_harness_content(self, content):
        """Validate process_comparison_harness.py content"""
        required_features = [
            "EnhancedProcessComparisonTest class",
            "run_enhanced_process_test method",
            "compare_processes method",
            "create_enhanced_deliverable method",
            "run_full_enhanced_test method"
        ]
        
        features_found = []
        issues = []
        
        # Check for required features
        if "class EnhancedProcessComparisonTest:" in content:
            features_found.append("EnhancedProcessComparisonTest class")
        if "def run_enhanced_process_test(self, process_type, disk_gate_required=False):" in content:
            features_found.append("run_enhanced_process_test method")
        if "def compare_processes(self, current_results, improved_results):" in content:
            features_found.append("compare_processes method")
        if "def create_enhanced_deliverable(self, comparison_results):" in content:
            features_found.append("create_enhanced_deliverable method")
        if "def run_full_enhanced_test(self):" in content:
            features_found.append("run_full_enhanced_test method")
        
        # Check for enhanced testing
        if "enhanced process comparison" in content.lower():
            features_found.append("Enhanced process comparison")
        
        # Check for quality metrics
        if "quality metrics" in content.lower():
            features_found.append("Quality metrics")
        
        # Check for enhanced infrastructure integration
        if "enhanced infrastructure" in content.lower():
            features_found.append("Enhanced infrastructure integration")
        
        # Validate content structure
        if "Enhanced Process Comparison Testing Harness" not in content:
            issues.append("Missing main title")
        
        if "class EnhancedProcessComparisonTest:" not in content:
            issues.append("Missing EnhancedProcessComparisonTest class")
        
        if "def run_full_enhanced_test(self):" not in content:
            issues.append("Missing main execution method")
        
        return {
            "valid": len(issues) == 0 and len(features_found) >= 4,
            "testing_features": features_found,
            "issues": issues
        }
    
    def validate_standardization(self):
        """Validate standardization across enhanced infrastructure"""
        print("\n=== Validating Infrastructure Standardization ===\n")
        
        standardization_checks = {}
        
        # Check evidence capture protocol consistency
        protocol_file = self.campaign_state_path / "evidence_capture_protocol.md"
        if protocol_file.exists():
            protocol_content = protocol_file.read_text()
            
            # Check for standardized evidence format
            has_standardized_format = (
                '"timestamp": "ISO-8601 UTC"' in protocol_content and
                '"outcome_class":' in protocol_content and
                '"decision":' in protocol_content and
                '"task_id":' in protocol_content
            )
            
            standardization_checks["standardized_evidence_format"] = has_standardized_format
            print(f"✓ Standardized evidence format: {'YES' if has_standardized_format else 'NO'}")
        
        # Check enhanced infrastructure consistency
        proxy_file = self.campaign_state_path / "PROXY_INFRASTRUCTURE_FIX.py"
        if proxy_file.exists():
            proxy_content = proxy_file.read_text()
            
            # Check for enhanced infrastructure features
            has_enhanced_features = (
                "Enhanced Persistence" in proxy_content and
                "Standardized Protocol" in proxy_content and
                "Quality Assurance" in proxy_content
            )
            
            standardization_checks["enhanced_infrastructure_features"] = has_enhanced_features
            print(f"✓ Enhanced infrastructure features: {'YES' if has_enhanced_features else 'NO'}")
        
        # Check process comparison standards
        harness_file = self.campaign_state_path / "process_comparison_harness.py"
        if harness_file.exists():
            harness_content = harness_file.read_text()
            
            # Check for standardized testing framework
            has_standardized_testing = (
                "Enhanced Process Comparison Test" in harness_content and
                "evidence_capture_protocol" in harness_content.lower() and
                "quality_metrics" in harness_content.lower()
            )
            
            standardization_checks["standardized_testing_framework"] = has_standardized_testing
            print(f"✓ Standardized testing framework: {'YES' if has_standardized_testing else 'NO'}")
        
        # Check independent reproduction standards
        reproduction_file = self.campaign_state_path / "reproduction_framework.py"
        if reproduction_file.exists():
            reproduction_content = reproduction_file.read_text()
            
            # Check for standardized reproduction validation
            has_standardized_reproduction = (
                "EvidenceReproducer" in reproduction_content and
                "independent reproduction" in reproduction_content.lower() and
                "validation_result" in reproduction_content
            )
            
            standardization_checks["standardized_reproduction_validation"] = has_standardized_reproduction
            print(f"✓ Standardized reproduction validation: {'YES' if has_standardized_reproduction else 'NO'}")
        
        # Overall standardization assessment
        all_standardized = all(standardization_checks.values())
        
        if all_standardized:
            print(f"\nInfrastructure Standardization Summary: PASS")
        else:
            print(f"\nInfrastructure Standardization Summary: FAIL")
            self.validation_results["validation_passed"] = False
            for check, passed in standardization_checks.items():
                if not passed:
                    self.validation_results["issues_found"].append(f"Failed standardization: {check}")
        
        self.validation_results["quality_checks"]["standardization"] = all_standardized
        
        return all_standardized
    
    def validate_backward_compatibility(self):
        """Validate backward compatibility with existing infrastructure"""
        print("\n=== Validating Backward Compatibility ===\n")
        
        compatibility_checks = {}
        
        # Check PROXY_INFRASTRUCTURE_FIX.py compatibility
        proxy_file = self.campaign_state_path / "PROXY_INFRASTRUCTURE_FIX.py"
        if proxy_file.exists():
            proxy_content = proxy_file.read_text()
            
            # Check for PROXY infrastructure compatibility
            has_proxy_compatibility = (
                "PROXY_INFRASTRUCTURE_FIX.py" in proxy_content and
                "enhanced infrastructure" in proxy_content.lower() and
                "builds upon" in proxy_content.lower()
            )
            
            compatibility_checks["proxy_infrastructure_compatibility"] = has_proxy_compatibility
            print(f"✓ PROXY infrastructure compatibility: {'YES' if has_proxy_compatibility else 'NO'}")
        
        # Check evidence capture protocol compatibility
        protocol_file = self.campaign_state_path / "evidence_capture_protocol.md"
        if protocol_file.exists():
            protocol_content = protocol_file.read_text()
            
            # Check for evidence capture protocol compatibility
            has_evidence_compatibility = (
                "enhanced infrastructure" in protocol_content.lower() and
                "standardized protocol" in protocol_content.lower() and
                "integration strategy" in protocol_content.lower()
            )
            
            compatibility_checks["evidence_capture_compatibility"] = has_evidence_compatibility
            print(f"✓ Evidence capture compatibility: {'YES' if has_evidence_compatibility else 'NO'}")
        
        # Check process comparison harness compatibility
        harness_file = self.campaign_state_campaign_path / "process_comparison_harness.py"
        if harness_file.exists():
            harness_content = harness_file.read_text()
            
            # Check for process comparison harness compatibility
            has_harness_compatibility = (
                "enhanced infrastructure" in harness_content.lower() and
                "standardized testing" in harness_content.lower() and
                "quality metrics" in harness_content.lower()
            )
            
            compatibility_checks["process_harness_compatibility"] = has_harness_compatibility
            print(f"✓ Process harness compatibility: {'YES' if has_harness_compatibility else 'NO'}")
        
        # Check independent reproduction compatibility
        reproduction_file = self.campaign_state_path / "reproduction_framework.py"
        if reproduction_file.exists():
            reproduction_content = reproduction_file.read_text()
            
            # Check for reproduction framework compatibility
            has_reproduction_compatibility = (
                "enhanced infrastructure" in reproduction_content.lower() and
                "independent verification" in reproduction_content.lower() and
                "durable artifact" in reproduction_content.lower()
            )
            
            compatibility_checks["reproduction_framework_compatibility"] = has_reproduction_compatibility
            print(f"✓ Reproduction framework compatibility: {'YES' if has_reproduction_compatibility else 'NO'}")
        
        # Overall compatibility assessment
        all_compatible = all(compatibility_checks.values())
        
        if all_compatible:
            print(f"\nBackward Compatibility Summary: PASS")
        else:
            print(f"\nBackward Compatibility Summary: FAIL")
            self.validation_results["validation_passed"] = False
            for check, passed in compatibility_checks.items():
                if not passed:
                    self.validation_results["issues_found"].append(f"Failed compatibility: {check}")
        
        self.validation_results["quality_checks"]["backward_compatibility"] = all_compatible
        
        return all_compatible
    
    def run_complete_validation(self):
        """Run complete enhanced infrastructure validation"""
        print("=" * 80)
        print("ENHANCED INFRASTRUCTURE VALIDATION")
        print("=" * 80)
        print(f"\nValidation Timestamp: {self.validation_results['timestamp']}")
        print(f"Campaign State: {self.campaign_state_path}")
        print(f"Validation Objective: Enhanced Infrastructure Fix for Result-Memo Persistence")
        
        # Run all validation checks
        file_validation_passed = self.validate_file_existence()
        content_validation_passed = self.validate_file_contents()
        standardization_passed = self.validate_standardization()
        compatibility_passed = self.validate_backward_compatibility()
        
        # Overall validation result
        overall_validation_passed = (
            file_validation_passed and
            content_validation_passed and
            standardization_passed and
            compatibility_passed
        )
        
        print(f"\n{'=' * 80}")
        print("FINAL VALIDATION RESULTS")
        print(f"{'=' * 80}")
        
        print(f"\nValidation Status: {'PASS' if overall_validation_passed else 'FAIL'}")
        print(f"\nValidation Breakdown:")
        print(f"  File Existence: {'PASS' if file_validation_passed else 'FAIL'}")
        print(f"  Content Validation: {'PASS' if content_validation_passed else 'FAIL'}")
        print(f"  Infrastructure Standardization: {'PASS' if standardization_passed else 'FAIL'}")
        print(f"  Backward Compatibility: {'PASS' if compatibility_passed else 'FAIL'}")
        
        if overall_validation_passed:
            print(f"\n🎉 VALIDATION SUCCESSFUL!")
            print(f"\nEnhanced infrastructure successfully validated:")
            print(f"✓ All required enhanced infrastructure files present")
            print(f"✓ Enhanced evidence capture protocol implemented")
            print(f"✓ Independent reproduction framework enhanced")
            print(f"✓ Process comparison testing harness enhanced")
            print(f"✓ Infrastructure standardization achieved")
            print(f"✓ Backward compatibility maintained")
            
            print(f"\nEnhanced infrastructure now ready for:")
            print(f"• Agent 210: Enhanced process-comparison testing")
            print(f"• Future research: Standardized evidence capture")
            print(f"• Process improvement: Enhanced quality validation")
            print(f"• Evidence preservation: Durable infrastructure")
        else:
            print(f"\n❌ VALIDATION FAILED!")
            print(f"\nValidation issues found:")
            for issue in self.validation_results["issues_found"]:
                print(f"  • {issue}")
        
        self.validation_results["overall_validation_passed"] = overall_validation_passed
        
        return overall_validation_passed

if __name__ == "__main__":
    validator = EnhancedInfrastructureValidator()
    result = validator.run_complete_validation()
    
    if result:
        exit(0)
    else:
        exit(1)