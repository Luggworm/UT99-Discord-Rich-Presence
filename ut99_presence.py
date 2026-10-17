import os
import socket
import time
import re
from pathlib import Path
import psutil
from pypresence import Presence

DISCORD_APPLICATION_ID = "1560958602464854036"
PORT = 29777
NAMES = {'unrealtournament.exe', 'ut99.exe'}
MODES = {'DM':'Deathmatch','CTF':'Capture the Flag','DOM':'Domination','AS':'Assault','MH':'Monster Hunt','BT':'BunnyTrack','JB':'Jailbreak','LMS':'Last Man Standing','TDM':'Team Deathmatch'}

# Campaign stage order supplied by the player. Tutorials are stage 0 and excluded from totals.
CAMPAIGN_STAGES = {
    'Deathmatch': ['dm-tutorial', 'dm-oblivion', 'dm-stalwart', 'dm-fractal',
                   'dm-turbine', 'dm-codex', 'dm-pressure', 'dm-grinder',
                   'dm-kgalleon', 'dm-zeto', 'dm-shrapnel', 'dm-liandri',
                   'dm-conveyor', 'dm-peak'],
    'Domination': ['dom-tutorial', 'dom-condemned', 'dom-ghardhen',
                   'dom-cryptic', 'dom-cinder', 'dom-gearbolt',
                   'dom-leadworks', 'dom-olden', 'dom-sesmar', 'dom-metaldream'],
    'Capture the Flag': ['ctf-tutorial', 'ctf-niven', 'ctf-face',
                         'ctf-eternalcave', 'ctf-coret', 'ctf-gauntlet',
                         'ctf-dreary', 'ctf-command', 'ctf-lavagiant',
                         'ctf-november'],
    'Assault': ['as-tutorial', 'as-frigate', 'as-hispeed', 'as-rook',
                'as-mazon', 'as-oceanfloor', 'as-overlord'],
    'Challenge': ['dm-phobos', 'dm-morpheus', 'dm-tempest', 'dm-hyperblast'],
}
# Five campaign saves are supported. Set the active slot (1-5) in
# campaign_save_slot.txt beside this script. Defaults to slot 1.
CAMPAIGN_SLOT_FILE = Path(__file__).with_name('campaign_save_slot.txt')

def active_campaign_slot():
    try:
        value = int(CAMPAIGN_SLOT_FILE.read_text(encoding='utf-8-sig').strip())
        return value - 1 if 1 <= value <= 5 else 0
    except (OSError, ValueError):
        return 0
DIFFICULTIES = ('Novice', 'Average', 'Experienced', 'Skilled',
                'Adept', 'Masterful', 'Inhuman', 'Godlike')

def locate_user_ini():
    """Prefer the active UT99 executable's System folder over any other install."""
    for proc in psutil.process_iter(['name', 'exe']):
        try:
            if (proc.info.get('name') or '').lower() in NAMES:
                exe = proc.info.get('exe')
                if exe:
                    candidate = Path(exe).parent / 'User.ini'
                    if candidate.is_file():
                        return candidate
        except (psutil.Error, OSError):
            pass
    # Optional explicit path in a plain text file next to this Python script.
    config = Path(__file__).with_name('ut99_user_ini_path.txt')
    if config.is_file():
        try:
            candidate = Path(config.read_text(encoding='utf-8-sig').strip().strip('"'))
            if candidate.is_file():
                return candidate
        except OSError:
            pass
    for candidate in (Path(__file__).parent / 'User.ini',
                      Path(__file__).parent / 'System' / 'User.ini'):
        if candidate.is_file():
            return candidate
    return None

def read_campaign_difficulty(path, slot):
    """Read-only parser for [UTMenu.SlotWindow] Saves[n]=difficulty followed by backslash-separated fields"""
    if path is None:
        return None
    try:
        contents = path.read_text(encoding='utf-8-sig', errors='replace')
    except OSError:
        return None
    section = False
    for line in contents.splitlines():
        line = line.strip()
        if line.startswith('[') and line.endswith(']'):
            section = line.lower() == '[utmenu.slotwindow]'
            continue
        if not section or line.startswith((';', '#')):
            continue
        match = re.match(r'^Saves\[(\d+)\]\s*=\s*(.*)$', line, re.I)
        if match and int(match.group(1)) == slot:
            first = match.group(2).split('\\', 1)[0].strip()
            if first.isdigit() and 0 <= int(first) < len(DIFFICULTIES):
                return DIFFICULTIES[int(first)]
            return None
    return None

def campaign_stage(map_key):
    # Challenge must be checked first, as all Challenge maps have DM- prefixes.
    for ladder in ('Challenge', 'Deathmatch', 'Domination', 'Capture the Flag', 'Assault'):
        maps = CAMPAIGN_STAGES[ladder]
        if map_key in maps:
            return (ladder, maps.index(map_key), len(maps) - 1) if maps[0].endswith('-tutorial') else (ladder, maps.index(map_key) + 1, len(maps))
    return None

def running():
    return any((p.info.get('name') or '').lower() in NAMES for p in psutil.process_iter(['name']))

# Add keys here after uploading each portrait to your Discord application.
FACE_ASSET_KEYS = {'face-commandoskins-grail'}

def read_selected_face(path):
    """Read only [DefaultPlayer] Face, not bot faces or model MultiSkins."""
    if path is None:
        return ''
    try:
        contents = path.read_text(encoding='utf-8-sig', errors='replace')
    except OSError:
        return ''
    in_section = False
    for line in contents.splitlines():
        line = line.strip()
        if line.startswith('[') and line.endswith(']'):
            in_section = line.lower() == '[defaultplayer]'
            continue
        if in_section and not line.startswith((';', '#')) and '=' in line:
            key, value = line.split('=', 1)
            if key.strip().lower() == 'face':
                return value.strip()
    return ''


def main():
    id_file = Path(__file__).with_name('discord_app_id.txt')
    # Shared public Rich Presence application; no setup prompt required.
    # Existing local override is supported for developers using their own assets.
    app_id = DISCORD_APPLICATION_ID
    if id_file.exists():
        override = id_file.read_text(encoding='utf-8-sig').strip()
        if override.isdecimal():
            app_id = override
    print('Discord application:', app_id, flush=True)
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock.bind(('127.0.0.1', PORT))
    sock.settimeout(1)
    print('Listening for UT99 bridge on 127.0.0.1:%d' % PORT, flush=True)
    rpc = None
    last = None
    last_image_selection = None
    game_start = None
    session_start = None
    match_start = None
    match_id = None
    map_name = ''
    game_class = ''
    human_count = None
    bot_count = None
    last_message = 0.0
    character_name = ''
    character_class = ''
    face_texture = ''
    last_face_debug = None
    selected_face = ''
    player_frags = None
    player_deaths = None
    frag_limit = None
    objective_limit = None
    objective_kind = None
    campaign_mode = False
    reset_ladder_lock = None  # Ignore the ladder screen that was active when Reset was clicked.
    last_save = time.monotonic()
    last_difficulty_check = -100.0
    campaign_difficulty = None
    difficulty_source = None
    difficulty_slot = None
    total_file = Path(__file__).with_name('total_playtime_seconds.txt')
    try:
        saved_total = max(0, float(total_file.read_text().strip())) if total_file.exists() else 0.0
    except (ValueError, OSError):
        saved_total = 0.0
    print('Saved total playtime: %d seconds' % saved_total, flush=True)

    def save_total():
        tmp = total_file.with_suffix('.tmp')
        tmp.write_text(str(int(saved_total)), encoding='utf-8')
        tmp.replace(total_file)

    try:
        while True:
            try:
                data, source = sock.recvfrom(1024)
                msg = data.decode('utf-8', errors='replace').strip()
                if source[0] == '127.0.0.1' and msg == 'UT99|RESET':
                    # Lock the current ladder screen until a different screen/map is observed.
                    reset_ladder_lock = (map_name.lower(), game_class.lower()) if (
                        map_name.lower() == 'ut-logo-map' and
                        game_class.lower() in ('botpack.laddernewgame', 'botpack.ladderloadgame')
                    ) else None
                    campaign_mode = False
                    map_name = ''
                    game_class = ''
                    match_id = None
                    match_start = None
                    human_count = bot_count = None
                    character_name = character_class = ''
                    face_texture = ''
                    player_frags = player_deaths = None
                    last_message = 0.0
                    last = None
                    print('PRESENCE RESET: campaign cleared; session timer preserved', flush=True)
                    continue
                if source[0] == '127.0.0.1' and msg.startswith('UT99|'):
                    parts = msg.split('|')
                    if len(parts) >= 3:
                        incoming_map = parts[1].strip()[:100]
                        incoming_id = parts[3].strip() if len(parts) >= 4 else None
                        if len(parts) >= 6:
                            try:
                                human_count = max(0, int(parts[4]))
                                bot_count = max(0, int(parts[5]))
                            except ValueError:
                                human_count = bot_count = None
                        else:
                            human_count = bot_count = None
                        # Optional bridge v3.26 fields: character, class, score, deaths.
                        # Do not retain stale stats when older bridge packets arrive.
                        character_name = parts[6].strip()[:80] if len(parts) > 6 else ''
                        character_class = parts[7].strip()[:80] if len(parts) > 7 else ''
                        face_texture = parts[10].strip()[:150] if len(parts) > 10 else ''
                        try:
                            frag_limit = int(parts[11]) if len(parts) > 11 and parts[11] else None
                        except ValueError:
                            frag_limit = None
                        try:
                            objective_limit = int(float(parts[12])) if len(parts) > 12 and parts[12] else None
                        except ValueError:
                            objective_limit = None
                        objective_kind = parts[13].strip() if len(parts) > 13 else None
                        try:
                            player_frags = int(float(parts[8])) if len(parts) > 8 and parts[8] else None
                            player_deaths = int(float(parts[9])) if len(parts) > 9 and parts[9] else None
                        except ValueError:
                            player_frags = player_deaths = None
                        if incoming_id and incoming_id != match_id:
                            match_id = incoming_id
                            match_start = int(time.time())
                            print('New match: timer reset:', incoming_map, flush=True)
                        elif incoming_map != map_name:
                            match_start = int(time.time())
                            print('Map changed: timer reset:', incoming_map, flush=True)
                        map_name = incoming_map
                        game_class = parts[2].strip()[:150]
                        incoming_screen = (incoming_map.lower(), game_class.lower())
                        if reset_ladder_lock is not None and incoming_screen != reset_ladder_lock:
                            reset_ladder_lock = None
                            print('RESET LOCK: cleared after leaving ladder screen', flush=True)
                        if (incoming_screen[0] == 'ut-logo-map' and
                                incoming_screen[1] in ('botpack.laddernewgame', 'botpack.ladderloadgame') and
                                reset_ladder_lock is None):
                            if not campaign_mode:
                                print('CAMPAIGN MODE: enabled', flush=True)
                            campaign_mode = True
                        last_message = time.monotonic()
                        print('Bridge:', map_name, parts[2], flush=True)
            except socket.timeout:
                pass

            now = time.monotonic()
            if now - last_difficulty_check >= 5:
                last_difficulty_check = now
                ini_path = locate_user_ini()
                selected_face = read_selected_face(ini_path)
                slot = active_campaign_slot()
                updated_difficulty = read_campaign_difficulty(ini_path, slot)
                if (updated_difficulty != campaign_difficulty or
                        ini_path != difficulty_source or slot != difficulty_slot):
                    campaign_difficulty = updated_difficulty
                    difficulty_source = ini_path
                    difficulty_slot = slot
                    print('CAMPAIGN DIFFICULTY: %s (slot %d, %s)' % (
                        campaign_difficulty or 'Unknown', slot + 1,
                        str(ini_path) if ini_path else 'User.ini not found'), flush=True)
            game = running()
            if game and game_start is None:
                game_start = now
                # Discord timer starts fresh for each UT99 process session.
                # Map changes and Main Menu transitions do not reset it.
                session_start = int(time.time())
                print('UT99 started; tracking Discord playtime', flush=True)
            if not game:
                if game_start is not None:
                    saved_total += now - game_start
                    game_start = None
                    session_start = None
                    save_total()
                    print('UT99 closed; total playtime saved', flush=True)
                if rpc:
                    try: rpc.clear(); rpc.close()
                    except Exception: pass
                rpc = None
                last = None
                last_image_selection = None
                match_start = None
                match_id = None
                map_name = ''
                game_class = ''
                human_count = bot_count = None
                character_name = character_class = ''
                face_texture = ''
                player_frags = player_deaths = None
                last_message = 0.0
                campaign_mode = False
                reset_ladder_lock = None
                time.sleep(1)
                continue

            total_seconds = int(saved_total + (now - game_start))
            total_hours, total_minutes = divmod(total_seconds // 60, 60)
            discord_playtime = 'Discord playtime: %dh %02dm' % (total_hours, total_minutes)
            # A match is active while the UnrealScript bridge sends heartbeats.
            in_match = bool(map_name and now - last_message < 10)
            if not in_match:
                human_count = bot_count = None
                character_name = character_class = ''
                face_texture = ''
                player_frags = player_deaths = None
                frag_limit = None
                match_start = None
                match_id = None
            current = map_name if in_match else ''
            # UT99 Tournament ladder character-creation screen (not a playable match).
            is_character_creation = (
                reset_ladder_lock is None and current.lower() == 'ut-logo-map'
                and game_class.lower() == 'botpack.laddernewgame'
            )
            is_campaign_continue = (
                reset_ladder_lock is None and current.lower() == 'ut-logo-map'
                and game_class.lower() == 'botpack.ladderloadgame'
            )
            # While locked, show Main Menu rather than the still-running ladder heartbeat.
            if reset_ladder_lock is not None and (current.lower(), game_class.lower()) == reset_ladder_lock:
                current = ''
            tutorial_classes = {
                'dm-tutorial': 'botpack.trainingdm',
                'dom-tutorial': 'botpack.trainingdom',
                'ctf-tutorial': 'botpack.trainingctf',
                'as-tutorial': 'botpack.trainingas',
            }
            is_campaign_tutorial = (
                current.lower() in tutorial_classes
                and game_class.lower() == tutorial_classes.get(current.lower())
            )
            prefix = current.split('-', 1)[0].upper() if '-' in current else ''
            mode = MODES.get(prefix, 'Custom game') if current else 'Main Menu'
            # LMS uses DM- maps: determine its mode from the UnrealScript game class.
            if current and ('lastmanstanding' in game_class.lower() or prefix == 'LMS'):
                mode = 'Last Man Standing'
            # Tournament Team Game / TeamGamePlus also uses DM maps.
            if current and ('tournamentteamgame' in game_class.lower() or 'teamgameplus' in game_class.lower()):
                mode = 'Team Deathmatch'
            # Monster Hunt maps vary in name; identify the actual game class too.
            is_monster_hunt = bool(current and (prefix == 'MH' or 'monsterhunt' in game_class.lower() or 'monster_hunt' in game_class.lower()))
            if is_monster_hunt:
                mode = 'Monster Hunt'
            # One shared logo for every BunnyTrack and Rocket Arena UT map.
            # Prefer the game class, since custom maps may not use BT-/RA- prefixes.
            cls = game_class.lower().replace('_', '').replace(' ', '')
            is_bunnytrack = bool(current and (prefix in ('BT', 'BUNNYTRACK') or 'bunnytrack' in cls or 'bunnytrack' in current.lower()))
            is_rocket_arena = bool(current and (prefix in ('RA', 'RAUT') or 'rocketarena' in cls or 'rocketarena' in current.lower()))
            if is_bunnytrack:
                mode = 'BunnyTrack'
            elif is_rocket_arena:
                mode = 'Rocket Arena UT'
            # UT99 may report original map names with ][ and sometimes a .unr suffix.
            clean_map = current.strip().rsplit('\\', 1)[-1].rsplit('/', 1)[-1]
            clean_map = re.sub(r'(?i)\.unr$', '', clean_map)
            key = clean_map.lower().replace('[', '').replace(']', '').replace(' ', '_')
            key = ''.join(c for c in key if c.isalnum() or c in '_-')
            dm_maps = (
                'agony arcanetemple barricade codex conveyor crane curse cybrosis '
                'deck16 fetid fractal gothic grinder healpod hyperblast kgalleon '
                'liandri malevolence mojo morbias morpheus oblivion peak phobos '
                'pressure pyramid shrapnel spacenoxx stalwart stalwartxl tempest turbine zeto'
            ).split()
            assets = {'dm-' + name: 'dm-' + name for name in dm_maps}
            ctf_maps = (
                'command coret cybrosis darji16 dreary eternalcave face gauntlet '
                'hallofgiants high hydro16 kosov lavagiant niven november '
                'noxion16 nucleus orbital'
            ).split()
            assets.update({'ctf-' + name: 'ctf-' + name for name in ctf_maps})
            assault_maps = 'frigate guardia hispeed mazon oceanfloor overlord rook'.split()
            assets.update({'as-' + name: 'as-' + name for name in assault_maps})
            domination_maps = (
                'cinder condemned cryptic gearbolt ghardhen lament leadworks ' 
                'metaldream olden sesmar'
            ).split()
            assets.update({'dom-' + name: 'dom-' + name for name in domination_maps})
            # Distinguish CTF-Face][ from CTF-Face before removing brackets.
            if clean_map.lower() == 'ctf-face][':
                key = 'ctf-face2'
            assets['ctf-face2'] = 'ctf-face2'
            assets['dm-deck16'] = 'deck16-fixed'
            menu_gif = 'https://media.tenor.com/iTzsJbK5V3MAAAAj/ut-ut99.gif'
            if not current or is_character_creation or is_campaign_continue:
                picture = menu_gif
            elif is_campaign_tutorial:
                picture = key
            elif is_monster_hunt:
                picture = 'monsterhunt'
            elif is_bunnytrack:
                picture = 'bunnytrack'
            elif is_rocket_arena:
                picture = 'rocketarena'
            else:
                picture = assets.get(key, 'ut99')
            image_selection = (current, key, picture) if current else ('Main Menu', '', menu_gif)
            if image_selection != last_image_selection:
                print('IMAGE DEBUG: map=%r key=%r asset=%r' % image_selection, flush=True)
                last_image_selection = image_selection
            if current and not (is_character_creation or is_campaign_continue):
                match_seconds = max(0, int(time.time()) - match_start) if match_start else 0
                match_hours, remainder = divmod(match_seconds, 3600)
                match_minutes, match_secs = divmod(remainder, 60)
                state_text = 'Match playtime: %02d:%02d:%02d' % (match_hours, match_minutes, match_secs)
            else:
                state_text = ''
            limit_hover = ''
            if objective_limit is not None and objective_limit > 0 and objective_kind in ('Capture Limit', 'Score Limit', 'Time Limit', 'Frag Limit'):
                limit_hover = ' | %s: %d%s' % (objective_kind, objective_limit, ' min' if objective_kind == 'Time Limit' else '')
            elif frag_limit is not None and frag_limit > 0:
                limit_hover = ' | Frag Limit: %d' % frag_limit
            payload = dict(details=(mode + ' | ' + current)[:128] if current else 'Main Menu',
                           large_image=picture, large_text=current or "Unreal Tournament '99")
            stage = campaign_stage(key) if (campaign_mode or is_campaign_tutorial) else None
            if is_character_creation:
                payload['details'] = 'Tournament Campaign | Character Creation'
                payload['large_text'] = 'Tournament Campaign | Character Creation'
            elif is_campaign_continue:
                payload['details'] = 'Tournament Campaign | Continue Tournament'
                payload['large_text'] = 'Tournament Campaign | Continue Tournament'
            elif (campaign_mode or is_campaign_tutorial) and current:
                ladder = stage[0] if stage else mode
                payload['large_text'] = ('Tournament Campaign - ' + ladder + ' | ' + current + limit_hover)[:128]
                payload['details'] = ('Difficulty: ' + (campaign_difficulty or 'Unknown'))[:128]
                playtime = state_text.replace('Match playtime:', 'Playtime:', 1) if state_text else 'Playtime: 00:00:00'
                if stage:
                    playtime += ' | %s - Stage %d/%d' % stage
                payload['state'] = playtime[:128]
            elif current:
                payload['state'] = state_text[:128]
                if human_count is not None and bot_count is not None:
                    payload['details'] = ('Players: %d' % (human_count + bot_count))[:128]
                    payload['large_text'] = (mode + ' | ' + current + limit_hover)[:128]
            # Display local character/score when the upgraded UnrealScript bridge reports them.
            # Map artwork remains the large image; no unuploaded small-image asset is assumed.
            if current and not (is_character_creation or is_campaign_continue or is_campaign_tutorial):
                if player_frags is not None and player_deaths is not None:
                    stats = 'Frags: %d | Deaths: %d' % (player_frags, player_deaths)
                    if campaign_mode:
                        # Show live stats alongside campaign difficulty; keep map hover uncluttered.
                        payload['details'] = (payload['details'] + ' | ' + stats)[:128]
                    else:
                        payload['details'] = stats[:128]
                if selected_face:
                    face_key = 'face-' + re.sub(r'[^a-z0-9_-]', '-', selected_face.lower()).strip('-')
                    if face_key in FACE_ASSET_KEYS:
                        payload['small_image'] = face_key
                        payload['small_text'] = 'Player face'
                    if (selected_face, face_key in FACE_ASSET_KEYS) != last_face_debug:
                        print('FACE DEBUG: selected=%r asset=%r uploaded=%s' %
                              (selected_face, face_key, face_key in FACE_ASSET_KEYS), flush=True)
                        last_face_debug = (selected_face, face_key in FACE_ASSET_KEYS)
            # Native Discord elapsed timer tracks only this UT99 launch.
            # Match transitions reset match_start, not session_start.
            if session_start:
                payload['start'] = session_start
            if rpc is None:
                try:
                    rpc = Presence(app_id)
                    rpc.connect()
                    last = None
                    print('Discord connected', flush=True)
                except Exception as e:
                    print('Discord connection failed:', e, flush=True)
                    rpc = None
            if rpc and payload != last:
                try:
                    rpc.update(**payload)
                    last = payload.copy()
                    print('Discord updated:', payload['details'], '|', state_text or 'session timer', flush=True)
                except Exception as e:
                    print('Discord update failed:', e, flush=True)
                    try: rpc.close()
                    except Exception: pass
                    rpc = None
            # Save periodically so abrupt shutdown loses at most ~30 seconds.
            if now - last_save >= 30:
                save_total_snapshot = saved_total + (now - game_start)
                try:
                    tmp = total_file.with_suffix('.tmp')
                    tmp.write_text(str(int(save_total_snapshot)), encoding='utf-8')
                    tmp.replace(total_file)
                    saved_total = save_total_snapshot
                    game_start = now
                except OSError as e:
                    print('Playtime save failed:', e, flush=True)
                last_save = now
    except KeyboardInterrupt:
        print('Stopped')
    finally:
        if game_start is not None:
            saved_total += time.monotonic() - game_start
            save_total()
        if rpc:
            try: rpc.clear(); rpc.close()
            except Exception: pass
        sock.close()

if __name__ == '__main__':
    main()
