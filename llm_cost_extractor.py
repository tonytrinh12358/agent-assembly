#!/usr/bin/env python3
"""
LLM-based Cost Extractor for Kitchen Renovation Analysis
Uses Bedrock Converse API to intelligently extract cost information from analysis text.
Works with any Bedrock model (Claude, Nova, Llama, etc.)
"""

import boto3
import json
from typing import Dict, Optional
from pydantic import BaseModel


class ExtractedCosts(BaseModel):
    """Extracted cost information with support for ranges"""
    total_cost: str = "$0 AUD"
    material_cost: str = "$0 AUD" 
    labor_cost: str = "$0 AUD"
    contingency_cost: str = "$0 AUD"
    cost_per_sqm: str = "$0 AUD"
    budget_range: str = "$0 - $0 AUD"
    has_valid_costs: bool = False


class LLMCostExtractor:
    """Use Bedrock Converse API to extract cost information from kitchen analysis text.
    Works with any Bedrock model (Claude, Nova, Llama, Titan, etc.)"""
    
    def __init__(self, region: str = "us-west-2"):
        self.bedrock = boto3.client('bedrock-runtime', region_name=region)
        self.model_id = "us.amazon.nova-premier-v1:0"
    
    def extract_costs(self, analysis_text: str) -> ExtractedCosts:
        """
        Use Bedrock Converse API to extract cost information from analysis text
        
        Args:
            analysis_text: The full analysis response text containing cost information
            
        Returns:
            ExtractedCosts object with extracted cost strings (can be ranges)
        """
        
        prompt = f"""
Please extract the kitchen renovation cost information from the following analysis text and format it consistently:

<analysis_text>
{analysis_text}
</analysis_text>

I need you to find and extract these specific cost values in Australian dollars (AUD):

1. **Total Project Cost** - The final total renovation cost
2. **Material Cost** - Total cost of all materials (wood, granite, tiles, etc.)
3. **Labor Cost** - Total labor/installation costs
4. **Contingency Cost** - Any contingency or buffer costs mentioned
5. **Cost Per Square Meter** - Cost per square meter if mentioned
6. **Budget Range** - Any budget range or min/max values mentioned

**Output Requirements:**
- Always include "AUD" in the cost strings
- Use commas for thousands (e.g., "$14,348 AUD")
- If a range is mentioned, use format like "$12,000 - $16,500 AUD"
- If only a single value is found, just use that value
- If a cost type isn't mentioned or is zero, use "$0 AUD"
- Round to whole dollars (no cents) for cleaner display

**Output Format:**
Return ONLY a JSON object with this exact structure:
{{
  "total_cost": "extracted total cost with AUD",
  "material_cost": "extracted material cost with AUD", 
  "labor_cost": "extracted labor cost with AUD",
  "contingency_cost": "extracted contingency cost with AUD",
  "cost_per_sqm": "extracted cost per sqm with AUD",
  "budget_range": "extracted budget range with AUD",
  "has_valid_costs": true/false
}}

Set "has_valid_costs" to true if you found meaningful cost data (non-zero values), false otherwise.
"""

        try:
            # Use Converse API which works with any Bedrock model
            response = self.bedrock.converse(
                modelId=self.model_id,
                messages=[
                    {
                        "role": "user",
                        "content": [
                            {
                                "text": prompt
                            }
                        ]
                    }
                ],
                inferenceConfig={
                    "maxTokens": 1000,
                    "temperature": 0.1
                }
            )
            
            # Extract text from Converse API response
            extracted_text = response['output']['message']['content'][0]['text'].strip()
            
            # Parse the JSON response
            try:
                # Remove any markdown formatting if present
                if extracted_text.startswith('```json'):
                    extracted_text = extracted_text.split('```json')[1].split('```')[0].strip()
                elif extracted_text.startswith('```'):
                    extracted_text = extracted_text.split('```')[1].split('```')[0].strip()
                
                cost_data = json.loads(extracted_text)
                return ExtractedCosts(**cost_data)
                
            except (json.JSONDecodeError, KeyError, TypeError) as e:
                print(f"Error parsing LLM cost extraction response: {e}")
                return ExtractedCosts(has_valid_costs=False)
                
        except Exception as e:
            print(f"Error calling Bedrock for cost extraction: {e}")
            return ExtractedCosts(has_valid_costs=False)


def extract_costs_with_llm(analysis_text: str, region: str = "us-west-2") -> ExtractedCosts:
    """
    Convenience function to extract costs using Bedrock Converse API
    
    Args:
        analysis_text: Analysis text containing cost information
        region: AWS region for Bedrock
        
    Returns:
        ExtractedCosts object with cost strings
    """
    extractor = LLMCostExtractor(region=region)
    return extractor.extract_costs(analysis_text)


if __name__ == "__main__":
    # Test with sample analysis text
    sample_text = """
    The kitchen renovation analysis shows the following costs:
    - Total material costs: $7,521.83 AUD
    - Total labor costs: $4,975.00 AUD  
    - Contingency (15%): $1,851.96 AUD
    - Final project total: $14,348.79 AUD
    - Cost per square metre: $549.99 AUD
    - Budget range: $12,196 - $16,499 AUD
    """
    
    print("🧪 Testing LLM Cost Extractor")
    print("=" * 50)
    
    try:
        costs = extract_costs_with_llm(sample_text)
        print("✅ LLM extraction successful!")
        print(f"Total Cost: {costs.total_cost}")
        print(f"Material Cost: {costs.material_cost}")
        print(f"Labor Cost: {costs.labor_cost}")
        print(f"Contingency: {costs.contingency_cost}")
        print(f"Cost per m²: {costs.cost_per_sqm}")
        print(f"Budget Range: {costs.budget_range}")
        print(f"Has Valid Costs: {costs.has_valid_costs}")
    except Exception as e:
        print(f"❌ Test failed: {e}")



