#!/usr/bin/env python3
"""
Batch Team Member Processor
Processes team member list and runs systematic research for each member
"""

import re
import json
import time
from pathlib import Path
import sys

# Add team profiling workflow
MAIA_ROOT = Path(__file__).resolve().parents[2]
sys.path.append(str(MAIA_ROOT / "claude" / "tools"))

try:
    from team_profiling_workflow import TeamProfilingWorkflow
except ImportError:
    print("❌ Team profiling workflow not found")
    sys.exit(1)

def parse_team_list(team_string: str) -> list:
    """Parse team member string into structured data"""
    
    # Pattern to match: "Name | Orro" <email@orro.group>
    pattern = r'"([^"]+) \| Orro" <([^>]+)>'
    matches = re.findall(pattern, team_string)
    
    team_members = []
    for name, email in matches:
        team_members.append({
            "name": name,
            "email": email,
            "role": "Unknown - To Be Determined"  # Since roles not provided
        })
    
    return team_members

def main():
    """Process the team list and run research"""
    
    # Team list from user
    team_data = '"Abdallah Ziadeh | Orro" <abdallah.ziadeh@orro.group>; "Alex Olver | Orro" <alex.olver@orro.group>; "Amrit Sohal | Orro" <amrit.sohal@orro.group>; "Anil Kumar | Orro" <anil.kumar@orro.group>; "Ashish Negi | Orro" <ashish.negi@orro.group>; "Bhishana GC | Orro" <bhishana.gc@orro.group>; "Chris Kemp | Orro" <chris.kemp@orro.group>; "Daksha Jain | Orro" <daksha.jain@orro.group>; "Daniel Dignadice | Orro" <daniel.dignadice@orro.group>; "Debbie Pender | Orro" <debbie.pender@orro.group>; "Deepika Sharma | Orro" <deepika.sharma@orro.group>; "Deo Manalata | Orro" <deo.manalata@orro.group>; "Dillon Loos | Orro" <dillon.loos@orro.group>; "Dion Jewell | Orro" <dion.jewell@orro.group>; "Donovan Carr | Orro" <donovan.carr@orro.group>; "Ehab Moazzam | Orro" <ehab.moazzam@orro.group>; "Eric Expression | Orro" <eric.expression@orro.group>; "Foram Pandya | Orro" <foram.pandya@orro.group>; "Franz Canizares | Orro" <franz.canizares@orro.group>; "Hamish Ridland | Orro" <hamish.ridland@orro.group>; "Hannah Youssef | Orro" <hannah.youssef@orro.group>; "Harpreet Kaur | Orro" <harpreet.kaur@orro.group>; "Jake Stones | Orro" <jake.stones@orro.group>; "Janice Tablarin | Orro" <janice.tablarin@orro.group>; "Jason Singh | Orro" <jason.singh@orro.group>; "Jennelyn Puno | Orro" <jennelyn.puno@orro.group>; "Kristy Schaeffer | Orro" <kristy.schaeffer@orro.group>; "Lakmal Marasinghe | Orro" <lakmal.marasinghe@orro.group>; "Lance Letran | Orro" <lance.letran@orro.group>; "Llewellyn Booth | Orro" <llewellyn.booth@orro.group>; "Luke Mason | Orro" <luke.mason@orro.group>; "Mamta Sharma | Orro" <mamta.sharma@orro.group>; "Mandeep Lally | Orro" <mandeep.lally@orro.group>; "Manikrishna Suddala | Orro" <manikrishna.suddala@orro.group>; "Michael Villaflor | Orro" <michael.villaflor@orro.group>; "Naythan Dawe | Orro" <naythan.dawe@orro.group>; "Olli Ojala | Orro" <olli.ojala@orro.group>; "Pawan Kaur | Orro" <pawan.kaur@orro.group>; "Peter Mustow | Orro" <peter.mustow@orro.group>; "Prasanta Panta | Orro" <prasanta.panta@orro.group>; "Rajat | Orro" <rajat@orro.group>; "Robert Quito | Orro" <robert.quito@orro.group>; "Sangeetha Murthy | Orro" <sangeetha.murthy@orro.group>; "Steve Daalmeyer | Orro" <steve.daalmeyer@orro.group>; "Tash Dadimuni | Orro" <tash.dadimuni@orro.group>; "Wenard Gonzal | Orro" <wenard.gonzal@orro.group>; "Xian-Yao Loh | Orro" <xian-yao.loh@orro.group>; "Zankrut Dhebar | Orro" <zankrut.dhebar@orro.group>'
    
    print("🔍 Processing Orro Team Member List...")
    
    # Parse team data
    team_members = parse_team_list(team_data)
    print(f"✅ Parsed {len(team_members)} team members")
    
    # Save team list
    team_list_file = MAIA_ROOT / "claude" / "data" / "team_intelligence" / "orro_team_list.json"
    team_list_file.parent.mkdir(parents=True, exist_ok=True)
    
    with open(team_list_file, 'w') as f:
        json.dump(team_members, f, indent=2)
    
    print(f"💾 Team list saved: {team_list_file}")
    
    # Display team summary
    print(f"\n👥 Orro Team Summary:")
    print(f"   • Total Members: {len(team_members)}")
    print(f"   • All emails: @orro.group domain")
    print(f"   • Roles: To be determined through research")
    
    # Initialize workflow
    workflow = TeamProfilingWorkflow()
    
    print(f"\n🚀 Starting batch research process...")
    print(f"⏱️  Estimated time: {len(team_members) * 30} seconds (30s per member)")
    
    # Research first 5 members as a test
    print(f"\n🔬 Research Phase - Processing first 5 members:")
    
    successful_researches = 0
    for i, member in enumerate(team_members[:5]):
        try:
            print(f"\n[{i+1}/5] Researching {member['name']}...")
            profile = workflow.research_team_member(
                member['name'], 
                member['role'], 
                member['email']
            )
            successful_researches += 1
            
            # Brief delay to avoid overwhelming services
            time.sleep(2)
            
        except Exception as e:
            print(f"⚠️  Error researching {member['name']}: {e}")
    
    print(f"\n✅ Initial research complete: {successful_researches}/5 successful")
    
    # Generate initial analysis
    print(f"\n📊 Generating initial team analysis...")
    try:
        analysis = workflow.analyze_team_dynamics()
        print("✅ Team analysis complete")
        
        # Generate report
        report = workflow.generate_team_report()
        print("\n" + "="*60)
        print("INITIAL TEAM INTELLIGENCE REPORT")
        print("="*60)
        print(report)
        
    except Exception as e:
        print(f"⚠️  Analysis error: {e}")
    
    print(f"\n🎯 Next Steps:")
    print(f"   1. Review initial profiles and analysis")
    print(f"   2. Run full batch: python3 team_profiling_workflow.py batch-all")
    print(f"   3. Refine research based on initial findings")
    print(f"   4. Build Phase 2 specialized agent based on insights")

if __name__ == "__main__":
    main()