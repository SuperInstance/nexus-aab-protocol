'''Nexus AAB Protocol — Agent Architecture Behavior codec, roles, capability negotiation.'''
import json, time, hashlib
from dataclasses import dataclass, field
from typing import List, Dict, Optional, Set

@dataclass
class Role:
    role_id: str; name: str; capabilities: Dict[str, float] = field(default_factory=dict)
    constraints: Dict[str, float] = field(default_factory=dict)
    max_instances: int = 1; priority: int = 0

@dataclass
class Behavior:
    behavior_id: str; name: str; preconditions: List[str] = field(default_factory=list)
    postconditions: List[str] = field(default_factory=list)
    resource_cost: Dict[str, float] = field(default_factory=dict)

@dataclass
class Capability:
    cap_id: str; name: str; proficiency: float = 0.0
    training_data: int = 0; last_used: float = 0

class BehaviorCodec:
    def encode(self, behavior: Behavior) -> Dict:
        return {"id": behavior.behavior_id, "name": behavior.name,
                "pre": behavior.preconditions, "post": behavior.postconditions,
                "cost": behavior.resource_cost,
                "hash": hashlib.sha256(json.dumps({"pre": behavior.preconditions,
                "post": behavior.postconditions}).encode()).hexdigest()[:12]}
    def decode(self, data: Dict) -> Behavior:
        return Behavior(data["id"], data["name"], data["pre"], data["post"], data.get("cost", {}))
    def diff(self, a: Behavior, b: Behavior) -> Dict:
        return {"added_pre": set(b.preconditions)-set(a.preconditions),
                "removed_pre": set(a.preconditions)-set(b.preconditions),
                "added_post": set(b.postconditions)-set(a.postconditions),
                "removed_post": set(a.postconditions)-set(b.postconditions)}

class CapabilityNegotiator:
    def __init__(self):
        self.roles: Dict[str, Role] = {}; self.capabilities: Dict[str, Capability] = {}
    def register_role(self, role: Role) -> None:
        self.roles[role.role_id] = role
    def register_capability(self, cap: Capability) -> None:
        self.capabilities[cap.cap_id] = cap
    def find_best_agent(self, required_caps: Dict[str, float]) -> Optional[str]:
        best_role = None; best_score = -1
        for rid, role in self.roles.items():
            score = 0
            for cap_name, min_prof in required_caps.items():
                prof = role.capabilities.get(cap_name, 0)
                if prof < min_prof: score = -1; break
                score += prof
            if score > best_score: best_score = score; best_role = rid
        return best_role
    def negotiate(self, role_id: str, requested_caps: List[str]) -> Dict:
        role = self.roles.get(role_id)
        if not role: return {"status": "unknown_role"}
        available = {}; missing = []
        for cap_name in requested_caps:
            prof = role.capabilities.get(cap_name, 0)
            if prof > 0: available[cap_name] = prof
            else: missing.append(cap_name)
        return {"status": "partial" if missing else "full",
                "available": available, "missing": missing}

def demo():
    print("=== AAB Protocol ===")
    codec = BehaviorCodec()
    b = Behavior("b1", "survey_area", ["has_sonar","battery>20"], ["area_mapped"],
                 {"battery_per_min": 0.05, "time_per_m2": 0.1})
    encoded = codec.encode(b)
    print(f"  Encoded: {encoded['id']} hash={encoded['hash']}")
    decoded = codec.decode(encoded)
    print(f"  Decoded: {decoded.name} pre={decoded.preconditions}")
    negotiator = CapabilityNegotiator()
    negotiator.register_role(Role("auv", "AUV", {"survey": 0.9, "nav": 0.8, "rescue": 0.0}))
    negotiator.register_role(Role("surface", "Surface", {"comms": 0.99, "nav": 0.6, "survey": 0.3}))
    best = negotiator.find_best_agent({"survey": 0.7, "nav": 0.5})
    print(f"  Best for survey+nav: {best}")
    neg = negotiator.negotiate("auv", ["survey", "nav", "rescue"])
    print(f"  AUV capabilities: {neg}")

if __name__ == "__main__": demo()
