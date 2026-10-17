# Changelog

All notable changes to UT99 Discord Rich Presence are documented here.

## [3.31] — Game-mode statistics and gameplay logo

### Added
- **Last Man Standing:** remaining lives, maximum lives, and frags; maximum lives shown on map hover.
- **Monster Hunt:** live lives, hunters, and monsters, with remaining match time shown on map hover.
- **Rocket Arena UT:** wins and flawless wins using Rocket Arena team statistics.
- **BunnyTrack:** run timer.
- **Capture the Flag / Domination:** score-aware display.
- **Assault:** match-time display.
- **Gameplay logo:** `ut99-icon` shown as the small Rich Presence image during matches, while the main menu keeps its own artwork without the small logo.

### Changed
- Mode-aware statistics replace the generic frags/deaths display where inappropriate.
- Last Man Standing shows **frags**, not deaths, alongside lives.
- Monster Hunt map hover shows a **time-left countdown**, rather than an incorrect score-limit label.

### Removed
- Character face portrait detection and display, including face-based Discord assets.

### Preserved
- Classic map artwork and custom mode images.
- Discord automatic connection using the project's shared application ID.
- Campaign stage tracking, save-slot difficulty, and campaign reset functionality.
- Full-session Discord timer and separate match/run timing.

### Testing
- The project creator confirmed working in-game behavior for Deathmatch, Team Deathmatch, Last Man Standing, Monster Hunt, Rocket Arena UT, BunnyTrack, Capture the Flag, Domination, and Assault.
- Third-party mod compatibility may vary with different mod builds.

## [3.30] — Character face support (superseded)

- Added selected character-face detection from `User.ini` for Discord Rich Presence.
- **Superseded by v3.31:** character portraits have been removed in favor of a consistent UT99 gameplay logo.
