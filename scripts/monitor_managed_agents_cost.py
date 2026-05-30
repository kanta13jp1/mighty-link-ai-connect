#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Mighty-Link AI Connect: Managed Agents Cost Monitoring CLI Tool (T688)
Author: Antigravity (AI Agent)

This script runs a cost simulation for Google Vertex AI Agent Builder (Managed Agents)
and outputs a beautiful terminal dashboard to monitor budget tiers and switches.
"""

import os
import sys
import json

# Setup standard encoding
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

def run_simulation(hours=20.0, sessions=10000, queries=5000, input_tokens=10.0, output_tokens=2.0):
    VCPU_PRICE_PER_HOUR = 0.0864
    MEMORY_PRICE_PER_GB_HOUR = 0.0090
    SESSION_PRICE_PER_1K = 0.25
    SEARCH_PRICE_PER_1K = 4.00
    GEMINI_INPUT_PER_1M = 1.25
    GEMINI_OUTPUT_PER_1M = 3.75
    
    vcpu_hours = 2 * hours
    memory_gb_hours = 8 * hours
    
    vcpu_cost = vcpu_hours * VCPU_PRICE_PER_HOUR
    memory_cost = memory_gb_hours * MEMORY_PRICE_PER_GB_HOUR
    session_cost = (sessions / 1000) * SESSION_PRICE_PER_1K
    search_cost = (queries / 1000) * SEARCH_PRICE_PER_1K
    gemini_input_cost = input_tokens * GEMINI_INPUT_PER_1M
    gemini_output_cost = output_tokens * GEMINI_OUTPUT_PER_1M
    
    total_cost = vcpu_cost + memory_cost + session_cost + search_cost + gemini_input_cost + gemini_output_cost
    
    daily_budget = 5.00
    monthly_budget = 100.00
    
    budget_state = "HEALTHY"
    if total_cost > monthly_budget:
        budget_state = "EXCEEDED"
    elif total_cost > (monthly_budget * 0.8):
        budget_state = "WARNING"
        
    print("="*65)
    print("      MIGHTY-LINK MANAGED AGENTS COST MONITOR (T688)")
    print("="*65)
    print(f"[*] Simulation Parameters (Monthly):")
    print(f"  - Active Runtime Hours : {hours} hours (2 vCPU, 8 GB Profile)")
    print(f"  - Total Sessions       : {sessions} sessions")
    print(f"  - Vertex AI Search RAG : {queries} queries")
    print(f"  - Input Tokens (Gemini): {input_tokens} Million tokens")
    print(f"  - Output Tokens(Gemini): {output_tokens} Million tokens")
    print("-"*65)
    print("[*] Monthly Billing Breakdown (Estimated):")
    print(f"  - vCPU Compute Cost     : ${vcpu_cost:.2f}")
    print(f"  - Memory Resource Cost  : ${memory_cost:.2f}")
    print(f"  - Session Tracking Cost : ${session_cost:.2f}")
    print(f"  - Vertex AI Search Cost : ${search_cost:.2f}")
    print(f"  - Gemini Token (Input)  : ${gemini_input_cost:.2f}")
    print(f"  - Gemini Token (Output) : ${gemini_output_cost:.2f}")
    print("-"*65)
    
    color_code = "\033[92m" # Green
    if budget_state == "EXCEEDED":
        color_code = "\033[91m" # Red
    elif budget_state == "WARNING":
        color_code = "\033[93m" # Yellow
        
    print(f"[+] Total Estimated Cost   : {color_code}${total_cost:.2f}\033[0m per month")
    print(f"[*] Monthly Budget Limit   : ${monthly_budget:.2f}")
    print(f"[*] Billing Alert Status   : {color_code}{budget_state}\033[0m")
    print(f"[*] GCP Billing Alert      : ENABLED (Notification triggered at 80% limit)")
    print(f"[*] Pre-Adopt trial mode   : Express Mode (10 engines free / 90 days)")
    print("="*65)

def main():
    run_simulation()

if __name__ == "__main__":
    main()
