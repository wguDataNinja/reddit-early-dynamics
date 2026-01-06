from __future__ import annotations

import json
import random
from dataclasses import dataclass
from datetime import datetime, timezone, timedelta
from pathlib import Path
from typing import Any, Optional

from src.phase2.start_marker import read_phase2_start_marker


def _iso_to_dt(s: str) -> datetime:
    return datetime.fromisoformat(s.replace("Z", "+00:00")).astimezone(timezone.utc)


def _dt_to_iso(dt: datetime) -> str:
    return dt.astimezone(timezone.utc).isoformat().replace("+00:00", "Z")


@dataclass
class PostState:
    post_id: str
    created_utc: float
    first_observed_utc: str
    first_observed_day_index: int
    eligible_for_recruitment: bool
    ever_seen_in_new: bool = False
    drop_from_new_utc: Optional[str] = None

    recruitment_day: Optional[int] = None
    recruitment_metric_value: Optional[int] = None
    cohort_bin: Optional[str] = None

    selection_random_seed: Optional[str] = None
    selection_random_method: Optional[str] = None
    selection_random_note: Optional[str] = None

    last_fetched_utc: Optional[str] = None
    next_due_utc: Optional[str] = None

    terminal_status: Optional[str] = None
    terminal_utc: Optional[str] = None


class CohortManager:
    def __init__(self, cohort_state_path: str, phase2_start_path: str):
        self.cohort_state_path = Path(cohort_state_path)
        self.phase2_start_path = phase2_start_path

        self.cohort_state_path.parent.mkdir(parents=True, exist_ok=True)

        self._posts: dict[str, PostState] = {}
        self._seen_in_new: set[str] = set()
        self._freeze_written: bool = False

        self.cohort_http_calls_this_run: int = 0

        self._load_state()

    def _load_state(self) -> None:
        if not self.cohort_state_path.exists():
            return

        for line in self.cohort_state_path.open("r", encoding="utf-8"):
            if not line.strip():
                continue
            try:
                ev = json.loads(line)
            except Exception:
                continue

            et = ev.get("event_type")
            if et == "cohort_freeze":
                self._freeze_written = True
                continue
            if et != "post_state":
                continue

            pid = ev.get("post_id")
            if not isinstance(pid, str):
                continue

            existing = self._posts.get(pid)
            if existing is None:
                try:
                    st = PostState(
                        post_id=pid,
                        created_utc=float(ev["created_utc"]),
                        first_observed_utc=str(ev["first_observed_utc"]),
                        first_observed_day_index=int(ev["first_observed_day_index"]),
                        eligible_for_recruitment=bool(ev["eligible_for_recruitment"]),
                    )
                except Exception:
                    continue
                self._posts[pid] = st
                existing = st

            # Persisted flag: ever_seen_in_new
            if ev.get("ever_seen_in_new") is True:
                existing.ever_seen_in_new = True
                self._seen_in_new.add(pid)

            for k in [
                "drop_from_new_utc",
                "recruitment_day",
                "recruitment_metric_value",
                "cohort_bin",
                "selection_random_seed",
                "selection_random_method",
                "selection_random_note",
                "last_fetched_utc",
                "next_due_utc",
                "terminal_status",
                "terminal_utc",
            ]:
                if k in ev:
                    setattr(existing, k, ev.get(k))

    def _append_event(self, obj: dict[str, Any]) -> None:
        with self.cohort_state_path.open("a", encoding="utf-8") as f:
            f.write(json.dumps(obj, ensure_ascii=False) + "\n")

    def _phase2_start_utc(self) -> datetime:
        marker = read_phase2_start_marker(self.phase2_start_path)
        if marker:
            return _iso_to_dt(marker)
        return datetime.now(timezone.utc)

    def _day_index_for_run(self, run_started_utc: str) -> int:
        start = self._phase2_start_utc()
        now = _iso_to_dt(run_started_utc)
        delta = now - start
        day = int(delta.total_seconds() // 86400) + 1
        return min(max(day, 1), 7)

    def ingest_listing_observations(
        self,
        run_started_utc: str,
        listing_rows_by_surface_paths: dict[str, str],
    ) -> None:
        day_idx = self._day_index_for_run(run_started_utc)

        new_ids_this_run: set[str] = set()

        for surface, path in listing_rows_by_surface_paths.items():
            p = Path(path)
            if not p.exists() or p.stat().st_size == 0:
                continue

            with p.open("r", encoding="utf-8") as f:
                for line in f:
                    try:
                        row = json.loads(line)
                    except Exception:
                        continue

                    pid = row.get("id")
                    created_utc = row.get("created_utc")
                    if not isinstance(pid, str):
                        continue
                    if not isinstance(created_utc, (int, float)):
                        continue

                    in_new = surface == "new"
                    if in_new:
                        new_ids_this_run.add(pid)

                    score = int(row.get("score", 0) or 0)
                    num_comments = int(row.get("num_comments", 0) or 0)
                    metric = score + num_comments

                    if pid not in self._posts:
                        eligible = day_idx in (1, 2)
                        st = PostState(
                            post_id=pid,
                            created_utc=float(created_utc),
                            first_observed_utc=run_started_utc,
                            first_observed_day_index=day_idx,
                            eligible_for_recruitment=eligible,
                        )

                        # Only /new sets the recruitment metric for eligible posts
                        if eligible and in_new:
                            st.recruitment_metric_value = metric

                        # Persist ever_seen_in_new only when first observed in /new
                        if in_new:
                            st.ever_seen_in_new = True
                            self._seen_in_new.add(pid)

                        self._posts[pid] = st

                        ev = {
                            "event_type": "post_state",
                            "event_utc": run_started_utc,
                            "post_id": pid,
                            "created_utc": st.created_utc,
                            "first_observed_utc": st.first_observed_utc,
                            "first_observed_day_index": st.first_observed_day_index,
                            "eligible_for_recruitment": st.eligible_for_recruitment,
                        }
                        if st.ever_seen_in_new:
                            ev["ever_seen_in_new"] = True
                        if st.recruitment_metric_value is not None:
                            ev["recruitment_metric_value"] = st.recruitment_metric_value
                        self._append_event(ev)

                    else:
                        st = self._posts[pid]

                        # Persist first time we ever see this post in /new
                        if in_new and not st.ever_seen_in_new:
                            st.ever_seen_in_new = True
                            self._seen_in_new.add(pid)
                            self._append_event(
                                {
                                    "event_type": "post_state",
                                    "event_utc": run_started_utc,
                                    "post_id": st.post_id,
                                    "created_utc": st.created_utc,
                                    "first_observed_utc": st.first_observed_utc,
                                    "first_observed_day_index": st.first_observed_day_index,
                                    "eligible_for_recruitment": st.eligible_for_recruitment,
                                    "ever_seen_in_new": True,
                                    "drop_from_new_utc": st.drop_from_new_utc,
                                    "recruitment_day": st.recruitment_day,
                                    "recruitment_metric_value": st.recruitment_metric_value,
                                    "cohort_bin": st.cohort_bin,
                                }
                            )

                        # Update recruitment metric only from /new, and persist only on change
                        if (
                            in_new
                            and st.eligible_for_recruitment
                            and st.recruitment_day is None
                        ):
                            prev = st.recruitment_metric_value
                            st.recruitment_metric_value = metric
                            if prev != st.recruitment_metric_value:
                                self._append_event(
                                    {
                                        "event_type": "post_state",
                                        "event_utc": run_started_utc,
                                        "post_id": st.post_id,
                                        "created_utc": st.created_utc,
                                        "first_observed_utc": st.first_observed_utc,
                                        "first_observed_day_index": st.first_observed_day_index,
                                        "eligible_for_recruitment": st.eligible_for_recruitment,
                                        "ever_seen_in_new": True if st.ever_seen_in_new else None,
                                        "drop_from_new_utc": st.drop_from_new_utc,
                                        "recruitment_day": st.recruitment_day,
                                        "recruitment_metric_value": st.recruitment_metric_value,
                                        "cohort_bin": st.cohort_bin,
                                    }
                                )

        # Drop detection uses persisted ever_seen_in_new set (rehydrated on load)
        dropped = {pid for pid in self._seen_in_new if pid not in new_ids_this_run}
        for pid in dropped:
            st = self._posts.get(pid)
            if st and st.drop_from_new_utc is None:
                st.drop_from_new_utc = run_started_utc
                self._append_event(
                    {
                        "event_type": "post_state",
                        "event_utc": run_started_utc,
                        "post_id": pid,
                        "created_utc": st.created_utc,
                        "first_observed_utc": st.first_observed_utc,
                        "first_observed_day_index": st.first_observed_day_index,
                        "eligible_for_recruitment": st.eligible_for_recruitment,
                        "ever_seen_in_new": True if st.ever_seen_in_new else None,
                        "drop_from_new_utc": st.drop_from_new_utc,
                        "recruitment_day": st.recruitment_day,
                        "recruitment_metric_value": st.recruitment_metric_value,
                        "cohort_bin": st.cohort_bin,
                    }
                )

        # Recruitment triggers: first run of Day 2 and Day 3
        if day_idx == 2:
            self._maybe_recruit_end_of_day1(run_started_utc)
        if day_idx == 3:
            self._maybe_recruit_end_of_day2_and_freeze(run_started_utc)

    def _projected_total_unique_posts(self, run_started_utc: str) -> int:
        start = self._phase2_start_utc()
        now = _iso_to_dt(run_started_utc)
        elapsed_days = max((now - start).total_seconds() / 86400.0, 1.0)
        observed = len(self._posts)
        projected = int(observed * (7.0 / elapsed_days))
        return max(projected, observed)

    def _target_cohort_size(self, run_started_utc: str) -> int:
        projected = self._projected_total_unique_posts(run_started_utc)
        return max(int(round(projected * 0.01)), 1)

    def _maybe_recruit_end_of_day1(self, event_utc: str) -> None:
        target = self._target_cohort_size(event_utc)
        day1_target = max(int(target * 0.5), 1)

        candidates = [
            st
            for st in self._posts.values()
            if st.eligible_for_recruitment
            and st.first_observed_day_index == 1
            and st.recruitment_day is None
            and isinstance(st.recruitment_metric_value, int)
        ]

        self._run_recruitment(
            event_utc=event_utc,
            recruitment_day=1,
            candidates=candidates,
            target_size=day1_target,
        )

    def _maybe_recruit_end_of_day2_and_freeze(self, event_utc: str) -> None:
        if self._freeze_written:
            return

        target = self._target_cohort_size(event_utc)
        already = [st for st in self._posts.values() if st.cohort_bin is not None]
        remaining = max(target - len(already), 0)

        candidates = [
            st
            for st in self._posts.values()
            if st.eligible_for_recruitment
            and st.first_observed_day_index in (1, 2)
            and st.recruitment_day is None
            and isinstance(st.recruitment_metric_value, int)
        ]

        self._run_recruitment(
            event_utc=event_utc,
            recruitment_day=2,
            candidates=candidates,
            target_size=remaining,
        )

        projected = self._projected_total_unique_posts(event_utc)
        projected_target = self._target_cohort_size(event_utc)
        selected_day1 = len([st for st in self._posts.values() if st.recruitment_day == 1])
        selected_day2 = len([st for st in self._posts.values() if st.recruitment_day == 2])
        final_size = len([st for st in self._posts.values() if st.cohort_bin is not None])

        self._append_event(
            {
                "event_type": "cohort_freeze",
                "event_utc": event_utc,
                "projected_total_unique_posts": projected,
                "projected_cohort_target_size": projected_target,
                "selected_size_day1": selected_day1,
                "selected_size_day2": selected_day2,
                "final_cohort_size": final_size,
            }
        )
        self._freeze_written = True

    def _run_recruitment(
        self,
        event_utc: str,
        recruitment_day: int,
        candidates: list[PostState],
        target_size: int,
    ) -> None:
        if target_size <= 0 or not candidates:
            return

        candidates.sort(key=lambda s: int(s.recruitment_metric_value or 0))
        n = len(candidates)
        if n == 0:
            return

        third = max(n // 3, 1)
        bins = {
            "low": candidates[:third],
            "mid": candidates[third: 2 * third],
            "high": candidates[2 * third:],
        }

        seed_base = f"{self._phase2_start_utc().strftime('%Y%m%d_%H%M%S')}|day{recruitment_day}|v1"
        selected: list[PostState] = []

        per_bin = max(target_size // 3, 0)
        remainder = target_size - (per_bin * 3)

        for bname in ["low", "mid", "high"]:
            b = bins[bname]
            if not b:
                continue
            take = per_bin + (1 if remainder > 0 else 0)
            if remainder > 0:
                remainder -= 1
            take = min(take, len(b))
            if take <= 0:
                continue

            seed = f"{seed_base}|bin={bname}"
            rng = random.Random(seed)
            picks = rng.sample(b, k=take)
            for st in picks:
                st.recruitment_day = recruitment_day
                st.cohort_bin = bname
                st.selection_random_seed = seed
                st.selection_random_method = "seeded_random_sample"
                selected.append(st)

        for st in selected:
            self._append_event(
                {
                    "event_type": "post_state",
                    "event_utc": event_utc,
                    "post_id": st.post_id,
                    "created_utc": st.created_utc,
                    "first_observed_utc": st.first_observed_utc,
                    "first_observed_day_index": st.first_observed_day_index,
                    "eligible_for_recruitment": st.eligible_for_recruitment,
                    "ever_seen_in_new": True if st.ever_seen_in_new else None,
                    "drop_from_new_utc": st.drop_from_new_utc,
                    "recruitment_day": st.recruitment_day,
                    "recruitment_metric_value": st.recruitment_metric_value,
                    "cohort_bin": st.cohort_bin,
                    "selection_random_seed": st.selection_random_seed,
                    "selection_random_method": st.selection_random_method,
                }
            )

    def _compute_next_due(self, st: PostState, now_utc: datetime) -> Optional[datetime]:
        if st.terminal_status is not None:
            return None
        if st.drop_from_new_utc is None:
            return None
        if st.cohort_bin is None:
            return None

        created = datetime.fromtimestamp(st.created_utc, tz=timezone.utc)
        age = now_utc - created
        if age < timedelta(hours=6):
            interval = timedelta(hours=1)
        elif age < timedelta(days=2):
            interval = timedelta(hours=6)
        elif age < timedelta(days=7):
            interval = timedelta(days=1)
        else:
            return None

        if st.last_fetched_utc is None:
            return max(_iso_to_dt(st.drop_from_new_utc), now_utc)

        return _iso_to_dt(st.last_fetched_utc) + interval

    def process_due_queue(
        self,
        reddit,
        run_started_utc: str,
        seen_ids: set[str],
    ) -> tuple[int, int, int, int, bool, Optional[str]]:
        self.cohort_http_calls_this_run = 0
        now_dt = _iso_to_dt(run_started_utc)

        for st in self._posts.values():
            if st.cohort_bin is None or st.terminal_status is not None:
                continue
            if st.drop_from_new_utc is None:
                continue
            if st.next_due_utc is None:
                nd = self._compute_next_due(st, now_dt)
                if nd is not None:
                    st.next_due_utc = _dt_to_iso(nd)
                    self._append_event(
                        {
                            "event_type": "post_state",
                            "event_utc": run_started_utc,
                            "post_id": st.post_id,
                            "created_utc": st.created_utc,
                            "first_observed_utc": st.first_observed_utc,
                            "first_observed_day_index": st.first_observed_day_index,
                            "eligible_for_recruitment": st.eligible_for_recruitment,
                            "ever_seen_in_new": True if st.ever_seen_in_new else None,
                            "drop_from_new_utc": st.drop_from_new_utc,
                            "recruitment_day": st.recruitment_day,
                            "recruitment_metric_value": st.recruitment_metric_value,
                            "cohort_bin": st.cohort_bin,
                            "next_due_utc": st.next_due_utc,
                        }
                    )

        due: list[PostState] = []
        for st in self._posts.values():
            if st.terminal_status is not None:
                continue
            if st.cohort_bin is None:
                continue
            if st.next_due_utc is None:
                continue
            if _iso_to_dt(st.next_due_utc) <= now_dt:
                due.append(st)

        due_before = len(due)
        dedup_skips = 0
        fetched = 0

        due_filtered: list[PostState] = []
        for st in due:
            if st.post_id in seen_ids:
                dedup_skips += 1
                continue
            due_filtered.append(st)

        for st in due_filtered:
            try:
                sub = reddit.submission(id=st.post_id)
                sub._fetch()
                self.cohort_http_calls_this_run += 1

                removed_by_cat = getattr(sub, "removed_by_category", None)
                if removed_by_cat is not None:
                    st.terminal_status = "removed"
                    st.terminal_utc = run_started_utc
                    st.next_due_utc = None
                else:
                    if getattr(sub, "author", None) is None:
                        st.terminal_status = "deleted"
                        st.terminal_utc = run_started_utc
                        st.next_due_utc = None

                st.last_fetched_utc = run_started_utc
                if st.terminal_status is None:
                    nd = self._compute_next_due(st, now_dt)
                    st.next_due_utc = _dt_to_iso(nd) if nd is not None else None

                self._append_event(
                    {
                        "event_type": "post_state",
                        "event_utc": run_started_utc,
                        "post_id": st.post_id,
                        "created_utc": st.created_utc,
                        "first_observed_utc": st.first_observed_utc,
                        "first_observed_day_index": st.first_observed_day_index,
                        "eligible_for_recruitment": st.eligible_for_recruitment,
                        "ever_seen_in_new": True if st.ever_seen_in_new else None,
                        "drop_from_new_utc": st.drop_from_new_utc,
                        "recruitment_day": st.recruitment_day,
                        "recruitment_metric_value": st.recruitment_metric_value,
                        "cohort_bin": st.cohort_bin,
                        "last_fetched_utc": st.last_fetched_utc,
                        "next_due_utc": st.next_due_utc,
                        "terminal_status": st.terminal_status,
                        "terminal_utc": st.terminal_utc,
                    }
                )

                fetched += 1
            except Exception:
                continue

        due_after = max(due_before - fetched - dedup_skips, 0)

        cohort_miss_flag = False
        cohort_miss_reason = None
        if due_before > 0 and fetched == 0 and dedup_skips < due_before:
            cohort_miss_flag = True
            cohort_miss_reason = "due_work_failed_to_execute"

        return due_before, due_after, dedup_skips, fetched, cohort_miss_flag, cohort_miss_reason