def select_playlist(available: list[str], playlist_arg: str | None = None) -> list[str]:
    """
    Returns list of selected playlist names, or empty list if 'All' is chosen.
    - playlist_arg: exact name, or comma-separated exact names for non-interactive use.
    - Interactive: enter 0 for all, a single number, or comma-separated numbers (e.g. 2,3,5).
    """
    if playlist_arg:
        available_lower = {n.lower(): n for n in available}
        names = [n.strip() for n in playlist_arg.split(",")]
        matched = [available_lower[n.lower()] for n in names if n.lower() in available_lower]
        unmatched = [n for n in names if n.lower() not in available_lower]
        if not unmatched:
            print(f"Using playlist(s): {', '.join(matched)}")
            return matched
        print(f"No exact match for: {', '.join(unmatched)}. Showing menu.")

    print("Available playlists:")
    print("  0. All playlists")
    for i, name in enumerate(available, 1):
        print(f"  {i}. {name}")

    while True:
        choice = input("Select playlist(s) (e.g. 1 or 2,3,5 or 0 for all): ").strip()
        if choice == "0":
            return []
        try:
            indices = [int(x.strip()) for x in choice.split(",")]
            if all(1 <= idx <= len(available) for idx in indices):
                return [available[idx - 1] for idx in indices]
        except ValueError:
            pass
        print(f"Please enter number(s) between 0 and {len(available)} (e.g. 1 or 2,3,5).")
