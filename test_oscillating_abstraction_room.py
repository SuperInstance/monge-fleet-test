#!/usr/bin/env python3
"""Tests for oscillating_abstraction_room.py"""

import math
import sys
import os
sys.path.insert(0, os.path.dirname(__file__))

from oscillating_abstraction_room import (
    OscillatingAbstractionRoom,
    RoomConverging,
    score_tile,
    keyword_weights_at,
    dominant_keyword_at,
    phase_name,
    simulated_tiles,
    measure_stability,
    shannon_entropy,
)

KEYWORDS = ['consensus', 'fleet', 'agent', 'room']


def test_keyword_weights_phase_dependence():
    """Keyword weights MUST change with phase."""
    w0 = keyword_weights_at(0, KEYWORDS, 4)
    wp2 = keyword_weights_at(math.pi/2, KEYWORDS, 4)
    wp = keyword_weights_at(math.pi, KEYWORDS, 4)
    w3p2 = keyword_weights_at(3*math.pi/2, KEYWORDS, 4)
    
    assert w0[KEYWORDS[0]] == 1.0, f"kw[0] should be 1.0 at phase 0, got {w0[KEYWORDS[0]]}"
    assert w0[KEYWORDS[1]] == 0.1, f"kw[1] should be 0.1 at phase 0, got {w0[KEYWORDS[1]]}"
    
    assert wp2[KEYWORDS[1]] == 1.0, f"kw[1] should be 1.0 at π/2"
    assert wp[KEYWORDS[2]] == 1.0, f"kw[2] should be 1.0 at π"
    assert w3p2[KEYWORDS[3]] == 1.0, f"kw[3] should be 1.0 at 3π/2"
    
    print("✅ test_keyword_weights_phase_dependence")


def test_score_specificity_bonus():
    """Score must reward SPECIFICITY, not keyword coverage."""
    weights = {'consensus': 1.0, 'fleet': 0.1, 'agent': 0.1, 'room': 0.1}
    
    specific = score_tile("kw0_consensus_only_A_000", KEYWORDS, weights)
    broad = score_tile("mixed_all_consensus_fleet_agent_room_E_000", KEYWORDS, weights)
    
    # Specific tile matching ONLY dominant keyword should score HIGHER
    assert specific > broad, f"Specific {specific} should > broad {broad}"
    assert specific > 0.8, f"Specific should be high ({specific})"
    assert broad < 1.0, f"Broad should be penalized ({broad})"
    
    print(f"✅ test_score_specificity_bonus: specific={specific:.4f} > broad={broad:.4f}")


def test_oscillation_effect():
    """Different tiles must surface at different phases."""
    tiles = simulated_tiles(KEYWORDS)
    room = OscillatingAbstractionRoom(keywords=KEYWORDS)
    room.plato_available = False
    room.tiles = tiles[:]
    
    # Score same tile at different phases
    consensus_tile = "kw0_consensus_only_A_000"
    fleet_tile = "kw1_fleet_only_B_000"
    
    s_c_at_0 = room.score(consensus_tile, 0)
    s_c_at_p2 = room.score(consensus_tile, math.pi/2)
    s_f_at_0 = room.score(fleet_tile, 0)
    s_f_at_p2 = room.score(fleet_tile, math.pi/2)
    
    assert s_c_at_0 > s_c_at_p2, f"consensus should score higher at phase 0 ({s_c_at_0} vs {s_c_at_p2})"
    assert s_f_at_p2 > s_f_at_0, f"fleet should score higher at π/2 ({s_f_at_p2} vs {s_f_at_0})"
    
    print(f"✅ test_oscillation_effect: consensus {s_c_at_0:.4f}→{s_c_at_p2:.4f}, fleet {s_f_at_0:.4f}→{s_f_at_p2:.4f}")


def test_top_tiles_change_with_phase():
    """top_tiles must return different tiles at different phases."""
    tiles = simulated_tiles(KEYWORDS)
    room = OscillatingAbstractionRoom(keywords=KEYWORDS)
    room.plato_available = False
    room.tiles = tiles[:]
    
    tops_0 = {c for c, _ in room.top_tiles(5, 0)}
    tops_p2 = {c for c, _ in room.top_tiles(5, math.pi/2)}
    tops_p = {c for c, _ in room.top_tiles(5, math.pi)}
    tops_3p2 = {c for c, _ in room.top_tiles(5, 3*math.pi/2)}
    
    # All four sets should be DIFFERENT
    assert tops_0 != tops_p2, "Phase 0 and π/2 should surface different tiles"
    assert tops_0 != tops_p, "Phase 0 and π should surface different tiles"
    assert tops_0 != tops_3p2, "Phase 0 and 3π/2 should surface different tiles"
    
    print(f"✅ test_top_tiles_change_with_phase: all phase pairs produce different top-5 sets")


def test_static_vs_oscillating():
    """Static room must have stability=1.0, oscillating < 1.0."""
    tiles = simulated_tiles(KEYWORDS)
    
    static = RoomConverging(KEYWORDS)
    for t in tiles:
        static.add_tile(t['content'])
    
    osc = OscillatingAbstractionRoom(keywords=KEYWORDS)
    osc.plato_available = False
    osc.tiles = tiles[:]
    
    s_stat = measure_stability(static, KEYWORDS)
    s_osc = measure_stability(osc, KEYWORDS)
    
    assert s_stat['stability'] == 1.0, f"Static should have stability 1.0, got {s_stat['stability']}"
    assert s_osc['stability'] < 1.0, f"Oscillating should have stability < 1.0, got {s_osc['stability']}"
    assert s_osc['stability'] <= 0.5, f"Oscillating stability should be ≤ 0.5, got {s_osc['stability']}"
    
    print(f"✅ test_static_vs_oscillating: static={s_stat['stability']}, oscillating={s_osc['stability']}")


def test_fleet_coordination():
    """Phase-diverse agents find their targets."""
    tiles = simulated_tiles(KEYWORDS)
    room = OscillatingAbstractionRoom(keywords=KEYWORDS)
    room.plato_available = False
    room.tiles = tiles[:]
    
    agents = [
        (KEYWORDS[0], 0),
        (KEYWORDS[1], math.pi/2),
        (KEYWORDS[2], math.pi),
        (KEYWORDS[3], 3*math.pi/2),
    ]
    
    hits = 0
    for target, phase in agents:
        tops = room.top_tiles(10, phase)
        hit = sum(1 for c, _ in tops if target in c.lower())
        assert hit >= 8, f"Agent tracking '{target}' @ {phase_name(phase)} should get >=8/10 hits, got {hit}"
        hits += 1
    
    print(f"✅ test_fleet_coordination: all 4 agents found their targets")


def test_novelty_discovery():
    """Oscillating room should surface more tile types over time."""
    tiles = simulated_tiles(KEYWORDS)
    osc = OscillatingAbstractionRoom(keywords=KEYWORDS)
    osc.plato_available = False
    osc.tiles = tiles[:]
    
    static = RoomConverging(KEYWORDS)
    for t in tiles:
        static.add_tile(t['content'])
    
    osc_types = []
    static_types = []
    
    for t in range(50):
        osc.tick(0.1)
        tops_o = osc.top_tiles(5)
        osc_types.extend([next((kw for kw in KEYWORDS if kw in c.lower()), 'mixed') for c, _ in tops_o])
        
        static.tick(0.1)
        tops_s = static.top_tiles(5)
        static_types.extend([next((kw for kw in KEYWORDS if kw in c.lower()), 'mixed') for c, _ in tops_s])
    
    s_entropy = shannon_entropy(static_types)
    o_entropy = shannon_entropy(osc_types)
    
    assert o_entropy > s_entropy, f"Oscillating entropy {o_entropy} should > static entropy {s_entropy}"
    assert o_entropy >= 1.0, f"Oscillating entropy should be >= 1.0 bits, got {o_entropy}"
    
    print(f"✅ test_novelty_discovery: osc entropy={o_entropy:.2f} > static entropy={s_entropy:.2f}")


def test_simulated_tiles_mutually_exclusive():
    """Each tile type should contain ONLY its keyword(s)."""
    tiles = simulated_tiles(KEYWORDS)
    kw0_tiles = [t for t in tiles if 'A_' in t['content']]
    kw1_tiles = [t for t in tiles if 'B_' in t['content']]
    kw2_tiles = [t for t in tiles if 'C_' in t['content']]
    kw3_tiles = [t for t in tiles if 'D_' in t['content']]
    mixed_tiles = [t for t in tiles if 'E_' in t['content']]
    
    assert len(kw0_tiles) == 50
    assert len(kw1_tiles) == 50
    assert len(kw2_tiles) == 50
    assert len(kw3_tiles) == 50
    assert len(mixed_tiles) == 50
    assert len(tiles) == 250
    
    # Kw0 tiles should NOT contain kw1, kw2, kw3
    for t in kw0_tiles:
        assert KEYWORDS[1] not in t['content'].lower(), f"kw0 tile shouldn't contain {KEYWORDS[1]}: {t}"
    
    # Mixed tiles should contain ALL
    for t in mixed_tiles:
        for kw in KEYWORDS:
            assert kw in t['content'].lower(), f"Mixed tile should contain {kw}: {t}"
    
    print(f"✅ test_simulated_tiles_mutually_exclusive: {len(tiles)} tiles, 5 groups")


def test_phase_name():
    """Phase name mapping must be correct."""
    assert phase_name(0) == '0'
    assert phase_name(math.pi/2 - 0.01) == '0'
    assert phase_name(math.pi/2 + 0.01) == 'π/2'
    assert phase_name(math.pi) == 'π'
    assert phase_name(3*math.pi/2) == '3π/2'
    assert phase_name(2*math.pi - 0.01) == '3π/2'
    print("✅ test_phase_name")


def test_dominant_keyword():
    """Dominant keyword at phase."""
    assert dominant_keyword_at(0, KEYWORDS, 4) == KEYWORDS[0]
    assert dominant_keyword_at(math.pi/2, KEYWORDS, 4) == KEYWORDS[1]
    assert dominant_keyword_at(math.pi, KEYWORDS, 4) == KEYWORDS[2]
    assert dominant_keyword_at(3*math.pi/2, KEYWORDS, 4) == KEYWORDS[3]
    print("✅ test_dominant_keyword")


def test_tick_advances_phase():
    """Advanced tick method: phase wraps at 2π."""
    room = OscillatingAbstractionRoom(keywords=KEYWORDS, period=4)
    room.plato_available = False
    
    # 4 ticks should complete one cycle
    phases = []
    for _ in range(5):
        phases.append(room.tick(1.0))
    
    assert abs(phases[0] - (2 * math.pi / 4)) < 0.001  # After 1 tick: π/2
    assert abs(phases[3]) < 0.001  # After 4 ticks: back to 0
    assert abs(phases[4] - (2 * math.pi / 4)) < 0.001  # After 5 ticks: π/2 again
    
    print(f"✅ test_tick_advances_phase: phase wraps at 2π")


if __name__ == "__main__":
    tests = [
        test_keyword_weights_phase_dependence,
        test_score_specificity_bonus,
        test_oscillation_effect,
        test_top_tiles_change_with_phase,
        test_static_vs_oscillating,
        test_fleet_coordination,
        test_novelty_discovery,
        test_simulated_tiles_mutually_exclusive,
        test_phase_name,
        test_dominant_keyword,
        test_tick_advances_phase,
    ]
    
    passed = 0
    failed = 0
    for test in tests:
        try:
            test()
            passed += 1
        except Exception as e:
            print(f"❌ {test.__name__}: {e}")
            failed += 1
    
    print(f"\n{'='*50}")
    print(f"Results: {passed}/{len(tests)} passed, {failed} failed")
    if failed > 0:
        sys.exit(1)
    else:
        print("All tests passed! ✅")
