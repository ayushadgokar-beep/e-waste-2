"""Min-conflicts scheduling with an exact CSP fallback for small job sets."""
import random


VALID_STATUSES = {"pending", "scheduled", "complete"}


def _duration(job):
    value = job.get("duration", 1)
    if isinstance(value, bool) or not isinstance(value, int) or value < 1:
        return None
    return value


def _slot_restriction(item, horizon, duration):
    """Return valid start slots, or all starts when no restriction is given."""
    slots = item.get("available_slots")
    valid_starts = set(range(max(0, horizon - duration + 1)))
    if slots is None:
        return valid_starts
    if not isinstance(slots, list):
        return set()
    return {slot for slot in slots if isinstance(slot, int) and not isinstance(slot, bool) and slot in valid_starts}


def schedule_jobs(jobs, benches, seed=7, max_steps=500, max_restarts=12):
    """Assign active jobs to compatible resources and non-overlapping start slots.

    Min-conflicts is attempted first. If its local search gets stuck, a small
    MRV backtracking CSP search is used to find a solution or prove that the
    supplied finite domains are unsatisfiable. Slots are zero-based starts;
    a duration of two occupies ``slot`` and ``slot + 1``.
    """
    if not isinstance(jobs, list) or not isinstance(benches, list):
        return {"success": False, "assignments": [], "conflicts": 0, "steps": 0,
                "unsatisfied": [{"job_id": None, "reason": "Jobs and resources must be lists."}]}
    active, completed, errors = [], [], []
    seen_ids = set()
    for index, job in enumerate(jobs):
        jid = job.get("id") if isinstance(job, dict) else None
        if not jid or jid in seen_ids:
            errors.append({"job_id": jid, "reason": "Each job must have a unique, non-empty ID."})
            continue
        seen_ids.add(jid)
        status = job.get("status", "pending")
        if status not in VALID_STATUSES:
            errors.append({"job_id": jid, "reason": f"Unsupported job status: {status}."})
            continue
        if status == "complete":
            completed.append(jid)
            continue
        duration = _duration(job)
        if duration is None:
            errors.append({"job_id": jid, "reason": "Duration must be a positive whole number of slots."})
            continue
        if not isinstance(job.get("type"), str) or not job["type"]:
            errors.append({"job_id": jid, "reason": "A processing type is required."})
            continue
        active.append(job)
    if errors:
        return {"success": False, "assignments": [], "conflicts": 0, "steps": 0,
                "unsatisfied": errors, "completed_jobs": completed, "algorithm": "min_conflicts+backtracking"}
    if not active:
        return {"success": True, "assignments": [], "conflicts": 0, "steps": 0,
                "unsatisfied": [], "completed_jobs": completed, "algorithm": "min_conflicts"}

    # The horizon allows all jobs to run sequentially if resource/slot domains permit.
    horizon = sum(_duration(job) for job in active)
    resources = {b.get("id"): b for b in benches if isinstance(b, dict) and b.get("id") and
                 isinstance(b.get("types"), list) and b.get("name")}
    domains = {}
    unsatisfied = []
    for job in active:
        jid = job["id"]
        compatible = [b for b in resources.values()
                      if job["type"] in b["types"] and
                      (not job.get("hazardous", False) or b.get("hazardous", False) is True)]
        starts = _slot_restriction(job, horizon, _duration(job))
        choices = []
        for bench in compatible:
            choices.extend((bench, slot) for slot in sorted(starts & _slot_restriction(bench, horizon, _duration(job))))
        if not choices:
            why = "No resource supports this processing type and hazard requirement."
            if compatible:
                why = "No valid start slot remains on any compatible resource for this job's duration."
            unsatisfied.append({"job_id": jid, "reason": why})
        domains[jid] = choices
    if unsatisfied:
        return {"success": False, "assignments": [], "conflicts": 0, "steps": 0,
                "unsatisfied": unsatisfied, "completed_jobs": completed, "algorithm": "min_conflicts+backtracking"}

    by_id = {job["id"]: job for job in active}

    def overlaps(jid, value, other_id, other_value):
        bench, slot = value
        other_bench, other_slot = other_value
        if bench["id"] != other_bench["id"] or bench.get("exclusive", True) is not True:
            return False
        return slot < other_slot + _duration(by_id[other_id]) and other_slot < slot + _duration(by_id[jid])

    def conflict_count(jid, value, assignment):
        return sum(1 for other_id, other_value in assignment.items()
                   if other_id != jid and overlaps(jid, value, other_id, other_value))

    rng = random.Random(seed)
    steps = 0
    solution = None
    # Random restarts keep min-conflicts from getting trapped in a local minimum.
    for _ in range(max_restarts):
        assignment = {jid: rng.choice(values) for jid, values in domains.items()}
        for _step in range(max_steps + 1):
            conflicted = [jid for jid, value in assignment.items() if conflict_count(jid, value, assignment)]
            if not conflicted:
                solution = assignment
                break
            jid = rng.choice(conflicted)
            scores = [(conflict_count(jid, value, assignment), value) for value in domains[jid]]
            least = min(score for score, _ in scores)
            candidates = [value for score, value in scores if score == least]
            assignment[jid] = rng.choice(candidates)
            steps += 1
        if solution is not None:
            break

    algorithm = "min_conflicts"
    if solution is None:
        # Exact CSP fallback: MRV variable ordering with forward checking.
        algorithm = "min_conflicts+backtracking"
        partial = {}

        def search(unassigned):
            if not unassigned:
                return dict(partial)
            jid = min(unassigned, key=lambda item: sum(
                not conflict_count(item, value, partial) for value in domains[item]))
            viable = [value for value in domains[jid] if not conflict_count(jid, value, partial)]
            for value in viable:
                partial[jid] = value
                result = search([item for item in unassigned if item != jid])
                if result is not None:
                    return result
                del partial[jid]
            return None

        solution = search(list(domains))
        if solution is None:
            details = [{"job_id": jid, "reason": "Every valid resource/start-slot choice conflicts with another job."}
                       for jid in domains]
            return {"success": False, "assignments": [], "conflicts": 0, "steps": steps,
                    "unsatisfied": details, "completed_jobs": completed, "algorithm": algorithm}

    assignments = [{"job_id": job["id"], "bench": solution[job["id"]][0]["name"],
                    "bench_id": solution[job["id"]][0]["id"], "slot": solution[job["id"]][1],
                    "duration": _duration(job)} for job in active]
    return {"success": True, "assignments": assignments, "conflicts": 0, "steps": steps,
            "unsatisfied": [], "completed_jobs": completed, "algorithm": algorithm}
