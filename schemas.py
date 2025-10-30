#!/usr/bin/env python3
"""
Pydantic schemas for structured kitchen renovation cost analysis
"""

from pydantic import BaseModel, Field
from typing import Optional, Dict, Any
from datetime import datetime


class MaterialCosts(BaseModel):
    """Material costs breakdown"""
    stainless_steel: Optional[float] = Field(default=0.0, description="Stainless steel appliance costs")
    wood: Optional[float] = Field(default=0.0, description="Wood cabinet costs")
    granite: Optional[float] = Field(default=0.0, description="Granite countertop costs")
    tile: Optional[float] = Field(default=0.0, description="Tile flooring costs")
    total_material_cost: float = Field(description="Total material costs in AUD")


class LaborCosts(BaseModel):
    """Labor costs breakdown"""
    kitchen_cabinets: Optional[float] = Field(default=0.0, description="Cabinet installation labor")
    granite_countertops: Optional[float] = Field(default=0.0, description="Countertop installation labor")
    tile_flooring: Optional[float] = Field(default=0.0, description="Flooring installation labor")
    appliances: Optional[float] = Field(default=0.0, description="Appliance installation labor")
    total_labor_cost: float = Field(description="Total labor costs in AUD")


class Contingency(BaseModel):
    """Contingency costs"""
    percentage: int = Field(default=15, description="Contingency percentage")
    amount: float = Field(description="Contingency amount in AUD")


class BudgetRange(BaseModel):
    """Budget range estimates"""
    lower_limit: float = Field(description="Lower budget limit in AUD")
    upper_limit: float = Field(description="Upper budget limit in AUD")


class CostBreakdown(BaseModel):
    """Complete cost breakdown structure"""
    material_costs: MaterialCosts
    labor_costs: LaborCosts
    contingency: Contingency
    final_project_total: float = Field(description="Final total project cost in AUD")
    cost_per_square_metre: float = Field(description="Cost per square metre in AUD")
    budget_range: BudgetRange


class StructuredKitchenEstimate(BaseModel):
    """Structured kitchen renovation cost estimate"""
    cost_breakdown: CostBreakdown
    
    def extract_costs(self) -> Dict[str, float]:
        """Extract costs in a standard format for UI display"""
        return {
            "total_cost": self.cost_breakdown.final_project_total,
            "material_cost": self.cost_breakdown.material_costs.total_material_cost,
            "labor_cost": self.cost_breakdown.labor_costs.total_labor_cost,
            "contingency_cost": self.cost_breakdown.contingency.amount,
            "cost_per_sqm": self.cost_breakdown.cost_per_square_metre,
            "budget_min": self.cost_breakdown.budget_range.lower_limit,
            "budget_max": self.cost_breakdown.budget_range.upper_limit
        }


def parse_kitchen_costs(response_text: str) -> Optional[Dict[str, float]]:
    """
    Parse kitchen costs using Pydantic validation from response text
    
    Returns standardized cost dictionary or None if parsing fails
    """
    import re
    import json
    
    # Try to extract JSON from response
    json_blocks = []
    
    # Look for fenced JSON blocks (capture the entire block content, not just first brace)
    fenced_matches = re.finditer(r"```json\s*([\s\S]*?)\s*```", response_text, re.IGNORECASE)
    for match in fenced_matches:
        json_blocks.append(match.group(1))
    
    # Look for inline JSON
    inline_matches = re.finditer(r'COST_DATA_JSON:\s*(\{[^}]+\})', response_text)
    for match in inline_matches:
        json_blocks.append(match.group(1))
    
    # Alternative schema (newer agent output)
    class AltMaterialTotals(BaseModel):
        stainless_steel: Optional[float] = 0.0
        wood: Optional[float] = 0.0
        granite: Optional[float] = 0.0
        tile: Optional[float] = 0.0
        total: float

    class AltLaborTotals(BaseModel):
        lower_bound: float
        upper_bound: float

    class AltContingency(BaseModel):
        percentage: int
        lower_bound: Optional[float] = 0.0
        upper_bound: Optional[float] = 0.0

    class AltFinalProjectTotal(BaseModel):
        lower_bound: float
        upper_bound: float

    class AltCostPerSqm(BaseModel):
        total_area: Optional[float] = 0.0
        lower_bound: float
        upper_bound: float

    class AltBudgetRange(BaseModel):
        lower_bound: float
        upper_bound: float

    class AltEstimate(BaseModel):
        total_material_costs: AltMaterialTotals
        total_labor_costs: AltLaborTotals
        contingency: Optional[AltContingency] = None
        final_project_total: AltFinalProjectTotal
        cost_per_square_metre: Optional[AltCostPerSqm] = None
        budget_range: Optional[AltBudgetRange] = None

        def extract_costs(self) -> Dict[str, float]:
            labor_avg = (self.total_labor_costs.lower_bound + self.total_labor_costs.upper_bound) / 2.0
            total_avg = (self.final_project_total.lower_bound + self.final_project_total.upper_bound) / 2.0
            return {
                "total_cost": total_avg,
                "material_cost": self.total_material_costs.total,
                "labor_cost": labor_avg,
                "contingency_cost": (self.contingency.lower_bound + self.contingency.upper_bound) / 2.0 if self.contingency and self.contingency.lower_bound is not None and self.contingency.upper_bound is not None else 0.0,
                "cost_per_sqm": (self.cost_per_square_metre.lower_bound + self.cost_per_square_metre.upper_bound) / 2.0 if self.cost_per_square_metre else 0.0,
                "budget_min": self.budget_range.lower_bound if self.budget_range else 0.0,
                "budget_max": self.budget_range.upper_bound if self.budget_range else 0.0,
            }

    def _extract_from_cost_breakdown(cost_root: Dict[str, Any]) -> Optional[Dict[str, float]]:
        try:
            # Material cost
            mat_block = cost_root.get('material_costs', {}) or {}
            material_cost = None
            # direct total
            if isinstance(mat_block, dict) and 'total_material_cost' in mat_block:
                material_cost = float(mat_block.get('total_material_cost') or 0)
            # sum nested entries with total_cost
            if (not material_cost) and isinstance(mat_block, dict):
                total_sum = 0.0
                found = False
                for v in mat_block.values():
                    if isinstance(v, dict) and 'total_cost' in v:
                        try:
                            total_sum += float(v.get('total_cost') or 0)
                            found = True
                        except Exception:
                            pass
                if found:
                    material_cost = total_sum
            material_cost = float(material_cost or 0.0)

            # Labor cost
            lab_block = cost_root.get('labor_costs', {}) or {}
            labor_cost = 0.0
            if isinstance(lab_block, dict):
                if 'total_labor_cost' in lab_block:
                    labor_cost = float(lab_block.get('total_labor_cost') or 0)
                else:
                    # average low/high if present
                    low = lab_block.get('low_end', {}) if isinstance(lab_block.get('low_end'), dict) else {}
                    high = lab_block.get('high_end', {}) if isinstance(lab_block.get('high_end'), dict) else {}
                    low_v = low.get('total_low_end_labor_cost') if isinstance(low, dict) else None
                    high_v = high.get('total_high_end_labor_cost') if isinstance(high, dict) else None
                    if low_v or high_v:
                        low_f = float(low_v or 0)
                        high_f = float(high_v or 0)
                        labor_cost = (low_f + high_f) / 2 if (low_v and high_v) else max(low_f, high_f)

            # Final project total
            final_total = cost_root.get('final_project_total')
            total_cost = 0.0
            if isinstance(final_total, (int, float)):
                total_cost = float(final_total)
            elif isinstance(final_total, dict):
                lo = float(final_total.get('low_end') or final_total.get('minimum') or 0)
                hi = float(final_total.get('high_end') or final_total.get('maximum') or 0)
                total_cost = (lo + hi) / 2 if (lo and hi) else max(lo, hi)

            # Contingency
            cont_block = cost_root.get('contingency', {}) or {}
            cont_amount = 0.0
            if isinstance(cont_block, dict):
                if 'amount' in cont_block:
                    cont_amount = float(cont_block.get('amount') or 0)
                elif 'lower_bound' in cont_block or 'upper_bound' in cont_block:
                    lo = float(cont_block.get('lower_bound') or 0)
                    hi = float(cont_block.get('upper_bound') or 0)
                    cont_amount = (lo + hi) / 2 if (lo and hi) else max(lo, hi)

            # Cost per sqm
            cpsm = cost_root.get('cost_per_square_metre')
            if isinstance(cpsm, (int, float)):
                cost_per_sqm = float(cpsm)
            elif isinstance(cpsm, dict):
                lo = float(cpsm.get('lower_bound') or 0)
                hi = float(cpsm.get('upper_bound') or 0)
                cost_per_sqm = (lo + hi) / 2 if (lo and hi) else max(lo, hi)
            else:
                cost_per_sqm = 0.0

            # Budget range
            br = cost_root.get('budget_range', {}) or {}
            budget_min = float(br.get('lower_bound') or 0) if isinstance(br, dict) else 0.0
            budget_max = float(br.get('upper_bound') or 0) if isinstance(br, dict) else 0.0

            # If total is zero but parts exist, compute total = materials + labor + contingency
            if total_cost == 0 and (material_cost or labor_cost or cont_amount):
                total_cost = float(material_cost + labor_cost + cont_amount)

            if any([material_cost, labor_cost, total_cost]):
                return {
                    'total_cost': total_cost,
                    'material_cost': material_cost,
                    'labor_cost': labor_cost,
                    'contingency_cost': cont_amount,
                    'cost_per_sqm': cost_per_sqm,
                    'budget_min': budget_min,
                    'budget_max': budget_max,
                }
        except Exception:
            return None
        return None

    # Try to parse each JSON block with Pydantic or flexible extractor
    for json_text in json_blocks:
        try:
            # Parse raw JSON
            raw_data = json.loads(json_text)
            
            # Try to create structured estimate
            if 'cost_breakdown' in raw_data:
                # 1) Try flexible extractor that tolerates nested shapes
                data = _extract_from_cost_breakdown(raw_data['cost_breakdown'])
                if data:
                    return data
                # 2) Try strict pydantic legacy schema
                try:
                    estimate = StructuredKitchenEstimate(**raw_data)
                    return estimate.extract_costs()
                except Exception:
                    pass
            else:
                # First try alternative schema (newer format)
                try:
                    alt = AltEstimate(**raw_data)
                    return alt.extract_costs()
                except Exception:
                    # Wrap in cost_breakdown and try legacy schema
                    wrapped_data = {'cost_breakdown': raw_data}
                    estimate = StructuredKitchenEstimate(**wrapped_data)
                    return estimate.extract_costs()
                
        except (json.JSONDecodeError, ValueError, KeyError) as e:
            continue
    
    return None


if __name__ == "__main__":
    # Test with sample data from the log
    sample_json = """```json
    {
      "cost_breakdown": {
        "material_costs": {
          "stainless_steel": 1721.47,
          "wood": 2100.00,
          "granite": 2250.00,
          "tile": 1480.00,
          "total_material_cost": 7551.47
        },
        "labor_costs": {
          "kitchen_cabinets": 1400.00,
          "granite_countertops": 937.50,
          "tile_flooring": 1387.50,
          "appliances": 500.00,
          "total_labor_cost": 4225.00
        },
        "contingency": {
          "percentage": 15,
          "amount": 1763.91
        },
        "final_project_total": 13540.38,
        "cost_per_square_metre": 246.19,
        "budget_range": {
          "lower_limit": 11509.32,
          "upper_limit": 15571.44
        }
      }
    }
    ```"""
    
    costs = parse_kitchen_costs(sample_json)
    if costs:
        print("✅ Pydantic parsing successful!")
        for key, value in costs.items():
            print(f"- {key}: ${value:,.2f} AUD")
    else:
        print("❌ Pydantic parsing failed")

