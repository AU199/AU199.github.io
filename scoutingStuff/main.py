import json
import pyodide_http
from pyodide.ffi import create_proxy, to_js
from js import document, localStorage, fetch, console, Object

# Enable fetch for urllib
pyodide_http.patch_all()

class TBAClient:
    """Client for The Blue Alliance API"""
    
    BASE_URL = "https://www.thebluealliance.com/api/v3"
    
    def __init__(self):
        self.api_key = None
        self.event_key = None
        self.team_number = None
        self.load_settings()
        
    def load_settings(self):
        """Load settings from localStorage"""
        try:
            self.api_key = localStorage.getItem('tba_api_key')
            self.event_key = localStorage.getItem('event_key')
            self.team_number = localStorage.getItem('team_number')
        except:
            pass
    
    def save_settings(self, api_key, event_key, team_number):
        """Save settings to localStorage"""
        localStorage.setItem('tba_api_key', api_key)
        localStorage.setItem('event_key', event_key)
        localStorage.setItem('team_number', team_number)
        self.api_key = api_key
        self.event_key = event_key
        self.team_number = team_number

    async def make_request(self, endpoint):
        """Make a request to TBA API"""
        if not self.api_key:
            console.error("No API key provided")
            return None

        url = f"{self.BASE_URL}/{endpoint}"

        try:
            headers_dict = {"X-TBA-Auth-Key": self.api_key.strip()}
            headers_js = to_js(headers_dict)

            console.log(f"Making request to: {url}")

            options = Object.fromEntries(to_js([
                ["method", "GET"],
                ["headers", headers_js]
            ]))

            response = await fetch(url, options)
            console.log(f"Response status: {response.status}")

            if response.status == 200:
                data = await response.json()
                return data.to_py()
            else:
                error_text = await response.text()
                console.error(f"API Error {response.status}: {error_text}")
                return None

        except Exception as e:
            console.error(f"Request failed: {str(e)}")
            return None

    async def get_event_info(self):
        """Get event information"""
        if not self.event_key:
            return None
        return await self.make_request(f"event/{self.event_key}")
    
    async def get_event_teams(self):
        """Get teams at event"""
        if not self.event_key:
            return None
        return await self.make_request(f"event/{self.event_key}/teams")
    
    async def get_event_rankings(self):
        """Get event rankings"""
        if not self.event_key:
            return None
        return await self.make_request(f"event/{self.event_key}/rankings")
    
    async def get_event_matches(self):
        """Get event matches"""
        if not self.event_key:
            return None
        return await self.make_request(f"event/{self.event_key}/matches")
    
    async def get_team_status(self, team_key):
        """Get team status at event"""
        if not self.event_key:
            return None
        return await self.make_request(f"team/{team_key}/event/{self.event_key}/status")
    
    async def get_event_oprs(self):
        """Get OPR, DPR, CCWM for event"""
        if not self.event_key:
            return None
        return await self.make_request(f"event/{self.event_key}/oprs")


class StatboticsClient:
    """
    Client for Statbotics REST API v3.
    
    Correct v3 base URL: https://api.statbotics.io/v3
    
    Key endpoints (all use query parameters, NOT path segments):
      GET /team_events?event={event_key}          -> list of team-event records
      GET /team_events?team={team}&event={event}  -> single team at event
      GET /team_matches?team={team}&event={event} -> match history for a team at event
      GET /matches?event={event_key}              -> all matches at event
    
    Key EPA fields in v3 response (post-2025 breaking changes):
      team_event record:
        team          -> int team number
        epa_start     -> float, EPA at event start
        epa_pre_elims -> float, EPA before eliminations
        epa_end       -> float, EPA at event end  (use this as "current event EPA")
        epa_mean      -> float, mean EPA across event
        norm_epa      -> float, normalized/unitless EPA (replaces norm_epa_end)
    """
    
    BASE_URL = "https://api.statbotics.io/v3"
    
    async def make_request(self, endpoint):
        """
        Make a GET request to the Statbotics v3 API.
        endpoint should include query string, e.g. 'team_events?event=2024cmptx'
        """
        url = f"{self.BASE_URL}/{endpoint}"
        try:
            console.log(f"[Statbotics] GET {url}")

            options = Object.fromEntries(to_js([
                ["method", "GET"],
            ]))

            response = await fetch(url, options)
            console.log(f"[Statbotics] Response status: {response.status}")

            if response.status == 200:
                data = await response.json()
                return data.to_py()
            else:
                err = await response.text()
                console.error(f"[Statbotics] {response.status}: {err}")
                return None
        except Exception as e:
            console.error(f"[Statbotics] request failed: {e}")
            return None

    # ---------- EVENT TEAMS ----------
    async def get_event_teams(self, event_key):
        """
        Returns list of team-event records for all teams at an event.
        Correct v3 endpoint: GET /team_events?event={event_key}
        Each record contains: team, epa_start, epa_pre_elims, epa_end, epa_mean, norm_epa, etc.
        """
        return await self.make_request(f"team_events?event={event_key}&limit=500")

    # ---------- SINGLE TEAM AT EVENT ----------
    async def get_team_event(self, team, event_key):
        """
        Returns EPA record for one team at a specific event.
        Correct v3 endpoint: GET /team_events?team={team}&event={event_key}
        Returns a list (usually one item).
        """
        result = await self.make_request(f"team_events?team={team}&event={event_key}")
        if result and len(result) > 0:
            return result[0]
        return None

    # ---------- TEAM MATCHES ----------
    async def get_team_matches(self, team, event_key):
        """
        Returns match history for a team at an event.
        Correct v3 endpoint: GET /team_matches?team={team}&event={event_key}
        """
        return await self.make_request(f"team_matches?team={team}&event={event_key}&limit=200")

    # ---------- EVENT MATCHES ----------
    async def get_event_matches(self, event_key):
        """
        Returns all matches at an event with predictions.
        Correct v3 endpoint: GET /matches?event={event_key}
        """
        return await self.make_request(f"matches?event={event_key}&limit=500")

    # ---------- SINGLE MATCH ----------
    async def get_match(self, match_key):
        """
        Returns a single match with prediction data.
        Correct v3 endpoint: GET /match/{match_key}
        """
        return await self.make_request(f"match/{match_key}")


def get_epa_from_record(team_record):
    """
    Safely extract EPA value from a Statbotics v3 team_event record.
    Tries epa_end first (current event EPA), falls back to epa_mean, then norm_epa.
    Returns a float or 0.
    """
    if not team_record:
        return 0
    # epa_end = EPA at end of event (best indicator of current performance)
    val = team_record.get('epa').get('total_points').get("mean")
    try:
        return float(val)
    except (TypeError, ValueError):
        return 0


def get_norm_epa_from_record(team_record):
    """
    Safely extract normalized/unitless EPA from a Statbotics v3 team_event record.
    In v3 the field is 'norm_epa' (previously 'norm_epa_end').
    Returns a float or 0.
    """
    if not team_record:
        print("no team record")
        return 0
    val = team_record.get('epa').get('unitless')
    try:
        return float(val)
    except (TypeError, ValueError):
        return 0


class Dashboard:
    """Main dashboard controller"""
    
    def __init__(self):
        self.client = TBAClient()
        self.statbotics = StatboticsClient()

        self.current_view = "scout"

        self.matches_data = None
        self.rankings_data = None
        self.oprs_data = None

        # Statbotics — list of team_event records for the whole event
        self.epa_data = None
        # Lookup dict: team_number_str -> team_event record (built from epa_data)
        self.epa_lookup = {}

        self.current_filter = "all"
        self.epa_type = "normal"

        self.setup_ui()
        self.check_initial_setup()

    
    def setup_ui(self):
        """Setup UI event handlers"""
        # Wizard navigation
        start_btn = document.getElementById('start-setup')
        if start_btn:
            start_btn.addEventListener('click', create_proxy(self.start_wizard))
        
        next_btn = document.getElementById('next-to-event')
        if next_btn:
            next_btn.addEventListener('click', create_proxy(self.go_to_event_step))
        
        back_btn = document.getElementById('back-to-api')
        if back_btn:
            back_btn.addEventListener('click', create_proxy(self.go_to_api_step))
        
        finish_btn = document.getElementById('finish-setup')
        if finish_btn:
            finish_btn.addEventListener('click', create_proxy(self.finish_wizard))
        
        # Settings
        settings_btn = document.getElementById('settings-btn')
        if settings_btn:
            settings_btn.addEventListener('click', create_proxy(self.open_settings))
        
        close_btn = document.getElementById('close-settings')
        if close_btn:
            close_btn.addEventListener('click', create_proxy(self.close_settings))
        
        save_btn = document.getElementById('save-settings')
        if save_btn:
            save_btn.addEventListener('click', create_proxy(self.save_settings))
        
        # Navigation buttons
        nav_btns = document.querySelectorAll('.nav-btn')
        for btn in nav_btns:
            btn.addEventListener('click', create_proxy(self.switch_view))
        
        # View all teams button
        view_all_btn = document.getElementById('view-all-teams')
        if view_all_btn:
            view_all_btn.addEventListener('click', create_proxy(lambda e: self.navigate_to('leaderboard')))
        
        # Open settings from my team page
        open_settings_myteam = document.getElementById('open-settings-from-myteam')
        if open_settings_myteam:
            open_settings_myteam.addEventListener('click', create_proxy(self.open_settings))
        
        # Schedule filter buttons
        filter_btns = document.querySelectorAll('.schedule-filter-btn')
        for btn in filter_btns:
            btn.addEventListener('click', create_proxy(self.filter_schedule))
        
        # Alliance builder EPA type selector
        epa_btns = document.querySelectorAll('.epa-type-btn')
        for btn in epa_btns:
            btn.addEventListener('click', create_proxy(self.switch_epa_type))
        
        # Calculate matchup button
        calc_btn = document.getElementById('calculate-matchup')
        if calc_btn:
            calc_btn.addEventListener('click', create_proxy(self.calculate_custom_matchup))
        
        # Back from analysis button
        back_btn = document.getElementById('back-from-analysis')
        if back_btn:
            back_btn.addEventListener('click', create_proxy(lambda e: self.navigate_to('schedule')))
    
    def switch_view(self, event):
        """Switch between views"""
        target = event.currentTarget
        view_name = target.getAttribute('data-view')
        self.navigate_to(view_name)
    
    def navigate_to(self, view_name):
        """Navigate to a specific view"""
        import asyncio
        
        # Hide all views
        views = document.querySelectorAll('.view-container')
        for view in views:
            view.classList.remove('active')
        
        # Show selected view
        target_view = document.getElementById(f'view-{view_name}')
        if target_view:
            target_view.classList.add('active')
        
        # Update nav buttons
        nav_btns = document.querySelectorAll('.nav-btn')
        for btn in nav_btns:
            btn.classList.remove('text-primary')
            btn.classList.add('text-gray-500')
            # Update icon fill
            icon = btn.querySelector('.material-symbols-outlined')
            if icon:
                icon.style.fontVariationSettings = "'FILL' 0"
        
        # Highlight active button
        active_btn = document.getElementById(f'nav-{view_name}')
        if active_btn:
            active_btn.classList.remove('text-gray-500')
            active_btn.classList.add('text-primary')
            icon = active_btn.querySelector('.material-symbols-outlined')
            if icon:
                icon.style.fontVariationSettings = "'FILL' 1"
        
        self.current_view = view_name
        
        # Load view-specific data
        if view_name == 'leaderboard':
            asyncio.create_task(self.load_full_leaderboard())
        elif view_name == 'myteam':
            asyncio.create_task(self.load_my_team_view())
        elif view_name == 'schedule':
            asyncio.create_task(self.load_schedule_view())
        elif view_name == 'builder':
            if not self.epa_data:
                asyncio.create_task(self.load_epa_data())
    
    def check_initial_setup(self):
        """Check if initial setup is needed"""
        if self.client.api_key and self.client.event_key:
            wizard = document.getElementById('setup-wizard')
            if wizard:
                wizard.style.display = 'none'
            self.update_sync_status(True)
            import asyncio
            asyncio.create_task(self.load_all_data())
        else:
            wizard = document.getElementById('setup-wizard')
            if wizard:
                wizard.style.display = 'flex'
    
    def start_wizard(self, event):
        """Start the setup wizard"""
        document.getElementById('step-welcome').classList.add('hidden')
        document.getElementById('step-api-key').classList.remove('hidden')
    
    async def go_to_event_step(self, event):
        """Go to event key step with API validation"""
        api_key = document.getElementById('wizard-api-key').value.strip()
        error_div = document.getElementById('api-key-error')
        
        if not api_key or len(api_key) < 10:
            error_div.innerHTML = '<p class="text-red-400 text-xs font-bold">⚠️ Please enter a valid API key</p>'
            error_div.classList.remove('hidden')
            return
        
        error_div.innerHTML = '<p class="text-yellow-400 text-xs font-bold">⏳ Validating API key...</p>'
        error_div.classList.remove('hidden')
        error_div.className = 'mt-2 p-3 bg-yellow-500/10 border border-yellow-500/30 rounded-lg'
        
        temp_client = TBAClient()
        temp_client.api_key = api_key
        
        try:
            test_result = await temp_client.make_request('status')
            
            if test_result is None:
                error_div.innerHTML = '<p class="text-red-400 text-xs font-bold">⚠️ Invalid API key. Please check and try again.</p>'
                error_div.className = 'mt-2 p-3 bg-red-500/10 border border-red-500/30 rounded-lg'
                return
            
            error_div.classList.add('hidden')
            document.getElementById('step-api-key').classList.add('hidden')
            document.getElementById('step-event-key').classList.remove('hidden')
            
        except Exception as e:
            console.error(f"API validation error: {str(e)}")
            error_div.innerHTML = '<p class="text-red-400 text-xs font-bold">⚠️ Could not validate API key. Check your connection.</p>'
            error_div.className = 'mt-2 p-3 bg-red-500/10 border border-red-500/30 rounded-lg'
    
    def go_to_api_step(self, event):
        """Go back to API key step"""
        document.getElementById('step-event-key').classList.add('hidden')
        document.getElementById('step-api-key').classList.remove('hidden')
    
    async def finish_wizard(self, event):
        """Finish wizard and save settings with validation"""
        api_key = document.getElementById('wizard-api-key').value.strip()
        event_key = document.getElementById('wizard-event-key').value.strip()
        team_number = document.getElementById('wizard-team-number').value.strip()
        error_div = document.getElementById('event-key-error')
        
        if not event_key or len(event_key) < 4:
            error_div.innerHTML = '<p class="text-red-400 text-xs font-bold">⚠️ Please enter a valid event key</p>'
            error_div.classList.remove('hidden')
            return
        
        error_div.innerHTML = '<p class="text-yellow-400 text-xs font-bold">⏳ Validating event key...</p>'
        error_div.classList.remove('hidden')
        error_div.className = 'mt-2 p-3 bg-yellow-500/10 border border-yellow-500/30 rounded-lg'
        
        temp_client = TBAClient()
        temp_client.api_key = api_key
        temp_client.event_key = event_key
        
        try:
            event_data = await temp_client.get_event_info()
            
            if event_data is None:
                error_div.innerHTML = '<p class="text-red-400 text-xs font-bold">⚠️ Event not found. Check the event key and try again.</p>'
                error_div.className = 'mt-2 p-3 bg-red-500/10 border border-red-500/30 rounded-lg'
                return
            
            error_div.classList.add('hidden')
            self.client.save_settings(api_key, event_key, team_number)
            
            document.getElementById('api-key-input').value = api_key
            document.getElementById('event-key-input').value = event_key
            document.getElementById('team-number-input').value = team_number
            
            document.getElementById('setup-wizard').style.display = 'none'
            self.update_sync_status(True)
            
            self.show_loading("Loading event data...")
            await self.load_all_data()
            
        except Exception as e:
            console.error(f"Event validation error: {str(e)}")
            error_div.innerHTML = '<p class="text-red-400 text-xs font-bold">⚠️ Could not validate event. Check your connection.</p>'
            error_div.className = 'mt-2 p-3 bg-red-500/10 border border-red-500/30 rounded-lg'
    
    def open_settings(self, event):
        """Open settings modal"""
        modal = document.getElementById('settings-modal')
        modal.classList.remove('hidden')
        modal.style.display = 'flex'
    
    def close_settings(self, event):
        """Close settings modal"""
        modal = document.getElementById('settings-modal')
        modal.classList.add('hidden')
        modal.style.display = 'none'
    
    async def save_settings(self, event):
        """Save settings and reload data"""
        api_key = document.getElementById('api-key-input').value.strip()
        event_key = document.getElementById('event-key-input').value.strip()
        team_number = document.getElementById('team-number-input').value.strip()
        
        if not api_key or not event_key:
            console.error("API Key and Event Key are required!")
            return
        
        self.client.save_settings(api_key, event_key, team_number)
        
        # Reset cached EPA data so it reloads for new event
        self.epa_data = None
        self.epa_lookup = {}
        
        modal = document.getElementById('settings-modal')
        modal.classList.add('hidden')
        modal.style.display = 'none'
        
        self.update_sync_status(True)
        await self.load_all_data()
    
    def update_sync_status(self, online):
        """Update sync status indicator"""
        indicator = document.getElementById('sync-indicator')
        status_text = document.getElementById('sync-status')
        
        if online:
            indicator.className = 'size-2 bg-primary rounded-full animate-pulse'
            status_text.textContent = 'Online'
        else:
            indicator.className = 'size-2 bg-gray-500 rounded-full'
            status_text.textContent = 'Offline'
    
    def show_loading(self, message="Loading event data..."):
        """Show loading overlay"""
        overlay = document.getElementById('loading-overlay')
        text = document.getElementById('loading-text')
        if overlay:
            text.textContent = message
            overlay.style.display = 'flex'
    
    def hide_loading(self):
        """Hide loading overlay"""
        overlay = document.getElementById('loading-overlay')
        if overlay:
            overlay.style.display = 'none'
    
    async def load_all_data(self):
        """Load all data from TBA and Statbotics"""
        self.show_loading("Loading event data...")
        
        try:
            await self.load_event_info()
            await self.load_matches()
            await self.load_rankings()
            # Pre-load EPA data in background so it's ready for other views
            await self.load_epa_data()
            
            self.hide_loading()
            
        except Exception as e:
            console.error(f"Error loading data: {str(e)}")
            self.hide_loading()
    
    async def load_event_info(self):
        """Load and display event information"""
        event_data = await self.client.get_event_info()
        if event_data:
            event_name = event_data.get('name', 'Unknown Event')
            if len(event_name) > 30:
                event_name = event_name[:27] + '...'
            document.getElementById('event-name').textContent = event_name
    
    async def load_matches(self):
        """Load and display match data"""
        self.matches_data = await self.client.get_event_matches()
        
        if not self.matches_data:
            return
        
        qual_matches = [m for m in self.matches_data if m.get('comp_level') == 'qm']
        total_matches = len(qual_matches)
        completed_matches = len([m for m in qual_matches if m.get('actual_time')])
        
        scores = []
        for match in qual_matches:
            if match.get('alliances'):
                red_score = match['alliances'].get('red', {}).get('score', 0)
                blue_score = match['alliances'].get('blue', {}).get('score', 0)
                if red_score and blue_score:
                    scores.append(red_score)
                    scores.append(blue_score)
        
        avg_score = sum(scores) / len(scores) if scores else 0
        
        document.getElementById('avg-score').textContent = f"{avg_score:.1f}"
        document.getElementById('total-matches').textContent = str(total_matches)
        
        if total_matches > 0:
            progress = (completed_matches / total_matches) * 100
            document.getElementById('progress-bar').style.width = f"{progress}%"
            document.getElementById('progress-text').textContent = f"{int(progress)}% of qualification matches completed"
            
            remaining = total_matches - completed_matches
            document.getElementById('event-status').textContent = f"Event in progress • {remaining} matches remaining"
        
        await self.load_upcoming_matches(qual_matches)
    
    async def load_upcoming_matches(self, matches):
        """Load upcoming matches"""
        upcoming = [m for m in matches if not m.get('actual_time')]
        upcoming.sort(key=lambda x: x.get('match_number', 0))
        
        container = document.getElementById('upcoming-matches')
        
        if not upcoming:
            container.innerHTML = '<div class="text-center text-gray-400 py-4"><p class="text-sm">No upcoming matches</p></div>'
            return
        
        html = ''
        for match in upcoming[:3]:
            match_num = match.get('match_number', '?')
            
            red_teams = match.get('alliances', {}).get('red', {}).get('team_keys', [])
            blue_teams = match.get('alliances', {}).get('blue', {}).get('team_keys', [])
            
            red_nums = ', '.join([t.replace('frc', '') for t in red_teams])
            blue_nums = ', '.join([t.replace('frc', '') for t in blue_teams])
            
            html += f'''
            <div class="flex items-center justify-between bg-black/40 p-3 rounded-lg">
                <div class="text-center px-2">
                    <p class="text-[10px] text-gray-400 uppercase">Match</p>
                    <p class="text-lg font-black text-white leading-none">Q{match_num}</p>
                </div>
                <div class="flex-1 flex justify-around items-center px-4">
                    <div class="flex flex-col items-center">
                        <span class="text-[10px] font-bold text-blue-400 uppercase">Blue</span>
                        <span class="text-sm font-bold text-white">{blue_nums}</span>
                    </div>
                    <span class="text-gray-500 font-bold">VS</span>
                    <div class="flex flex-col items-center">
                        <span class="text-[10px] font-bold text-red-400 uppercase">Red</span>
                        <span class="text-sm font-bold text-white">{red_nums}</span>
                    </div>
                </div>
                <div class="text-right">
                    <span class="material-symbols-outlined text-primary">arrow_forward_ios</span>
                </div>
            </div>
            '''
        
        container.innerHTML = html
    
    async def load_rankings(self):
        """Load and display team rankings"""
        self.rankings_data = await self.client.get_event_rankings()
        self.oprs_data = await self.client.get_event_oprs()
        
        if not self.rankings_data or not self.rankings_data.get('rankings'):
            return
        
        rankings = self.rankings_data['rankings']
        oprs = self.oprs_data.get('oprs', {}) if self.oprs_data else {}
        
        document.getElementById('total-teams').textContent = str(len(rankings))
        
        # Show top 10 teams on main page
        container = document.getElementById('leaderboard-preview')
        html = ''
        
        for i, team_data in enumerate(rankings[:10]):
            html += self.render_team_card(team_data, oprs, i)
        
        container.innerHTML = html
    
    def render_team_card(self, team_data, oprs, index):
        """Render a single team card"""
        rank = team_data.get('rank', index + 1)
        team_key = team_data.get('team_key', '')
        team_num = team_key.replace('frc', '')
        
        opr = oprs.get(team_key, 0)
        opr_text = f"{opr:.1f} OPR" if opr else "N/A"
        
        record = team_data.get('record', {})
        wins = record.get('wins', 0)
        losses = record.get('losses', 0)
        ties = record.get('ties', 0)
        
        border_class = 'border-l-primary' if rank <= 3 else 'border-l-white/10'
        text_color = 'text-primary' if rank <= 3 else 'text-white'
        
        badge = '<span class="bg-primary/10 text-primary text-[10px] px-1.5 py-0.5 rounded font-bold uppercase">Pro</span>' if rank == 1 else ''
        
        return f'''
        <div class="glass-card rounded-lg p-3 flex items-center justify-between border-l-4 {border_class}">
            <div class="flex items-center gap-4">
                <div class="text-2xl font-black text-white/20 italic">#{rank}</div>
                <div>
                    <div class="flex items-center gap-2">
                        <span class="text-lg font-bold text-white leading-none">{team_num}</span>
                        {badge}
                    </div>
                    <p class="text-xs text-gray-400">{wins}-{losses}-{ties}</p>
                </div>
            </div>
            <div class="flex flex-col items-end">
                <span class="text-xs font-bold {text_color}">{opr_text}</span>
                <div class="flex gap-0.5 mt-1">
                    <div class="h-4 w-1 bg-primary/60"></div>
                    <div class="h-3 w-1 bg-primary/40"></div>
                    <div class="h-5 w-1 bg-primary/80"></div>
                    <div class="h-4 w-1 bg-primary/50"></div>
                </div>
            </div>
        </div>
        '''
    
    async def load_full_leaderboard(self):
        """Load full leaderboard view"""
        if not self.rankings_data:
            await self.load_rankings()
        
        if not self.rankings_data or not self.rankings_data.get('rankings'):
            return
        
        rankings = self.rankings_data['rankings']
        oprs = self.oprs_data.get('oprs', {}) if self.oprs_data else {}
        
        container = document.getElementById('full-leaderboard')
        html = ''
        
        for i, team_data in enumerate(rankings):
            html += self.render_team_card(team_data, oprs, i)
        
        container.innerHTML = html
    
    async def load_my_team_view(self):
        """Load My Team view"""
        if not self.client.team_number:
            document.getElementById('no-team-message').classList.remove('hidden')
            document.getElementById('myteam-content').classList.add('hidden')
            document.getElementById('myteam-subtitle').textContent = 'Configure your team in settings'
            return
        
        document.getElementById('no-team-message').classList.add('hidden')
        document.getElementById('myteam-content').classList.remove('hidden')
        document.getElementById('myteam-subtitle').textContent = f'Detailed analytics for Team {self.client.team_number}'
        
        team_key = f"frc{self.client.team_number}"
        
        # Update team number display
        document.getElementById('display-team-number').textContent = self.client.team_number
        
        # Load team status from TBA
        status = await self.client.get_team_status(team_key)
        
        if status:
            qual = status.get('qual', {})
            ranking = qual.get('ranking', {})
            rank = ranking.get('rank', '--')
            
            document.getElementById('my-team-rank').textContent = f"#{rank}"
            
            record = ranking.get('record', {})
            wins = record.get('wins', 0)
            losses = record.get('losses', 0)
            ties = record.get('ties', 0)
            
            document.getElementById('my-team-record').textContent = f"{wins}-{losses}-{ties}"
        
        # Calculate average score from TBA match data
        if not self.matches_data:
            self.matches_data = await self.client.get_event_matches()
        
        if self.matches_data:
            team_scores = []
            for match in self.matches_data:
                if not match.get('actual_time'):
                    continue
                
                alliances = match.get('alliances', {})
                for color in ['red', 'blue']:
                    teams = alliances.get(color, {}).get('team_keys', [])
                    if team_key in teams:
                        score = alliances.get(color, {}).get('score')
                        if score:
                            team_scores.append(score)
            
            if team_scores:
                avg = sum(team_scores) / len(team_scores)
                document.getElementById('my-team-avg').textContent = f"{avg:.1f}"
        
        # Get EPA from Statbotics using correct v3 endpoint
        if not self.epa_data:
            await self.load_epa_data()
        
        team_num_str = self.client.team_number
        if team_num_str in self.epa_lookup:
            team_record = self.epa_lookup[team_num_str]
            epa = get_epa_from_record(team_record)
            document.getElementById('my-team-epa').textContent = f"{epa:.1f}"
        else:
            document.getElementById('my-team-epa').textContent = "N/A"
        
        # Load next and previous matches
        await self.load_my_team_matches(team_key)
    
    async def load_my_team_matches(self, team_key):
        """Load next match, previous match, and win probability for my team"""
        if not self.matches_data:
            return
        
        qual_matches = [m for m in self.matches_data if m.get('comp_level') == 'qm']
        qual_matches.sort(key=lambda x: x.get('match_number', 0))
        
        # Find team's matches
        team_matches = []
        for match in qual_matches:
            alliances = match.get('alliances', {})
            red_teams = alliances.get('red', {}).get('team_keys', [])
            blue_teams = alliances.get('blue', {}).get('team_keys', [])
            if team_key in red_teams or team_key in blue_teams:
                team_matches.append(match)
        
        # Find next and previous matches
        next_match = None
        prev_match = None
        
        for match in team_matches:
            if match.get('actual_time'):
                prev_match = match
            else:
                if next_match is None:
                    next_match = match
                break
        
        # Render next match
        self.render_next_match(next_match, team_key)
        
        # Render previous match
        self.render_previous_match(prev_match, team_key)
        
        # Calculate and render win probability
        await self.calculate_win_probability(next_match, team_key)
    
    def render_next_match(self, match, team_key):
        """Render next match card"""
        container = document.getElementById('next-match-content')
        
        if not match:
            container.innerHTML = '<div class="text-center text-gray-400 py-4"><p class="text-sm">No upcoming matches</p></div>'
            return
        
        match_num = match.get('match_number', '?')
        alliances = match.get('alliances', {})
        
        red_teams = alliances.get('red', {}).get('team_keys', [])
        blue_teams = alliances.get('blue', {}).get('team_keys', [])
        
        # Determine our alliance
        our_color = 'red' if team_key in red_teams else 'blue'
        our_alliance = red_teams if our_color == 'red' else blue_teams
        opponent_alliance = blue_teams if our_color == 'red' else red_teams
        
        our_nums = ', '.join([f"<span class='font-bold'>{t.replace('frc', '')}</span>" if t == team_key else t.replace('frc', '') for t in our_alliance])
        opp_nums = ', '.join([t.replace('frc', '') for t in opponent_alliance])
        
        our_color_class = 'text-red-400 border-red-400/30' if our_color == 'red' else 'text-blue-400 border-blue-400/30'
        opp_color_class = 'text-blue-400' if our_color == 'red' else 'text-red-400'
        
        html = f'''
        <div class="bg-black/40 rounded-lg p-4 border-2 {our_color_class}">
            <div class="text-center mb-4">
                <p class="text-[10px] text-gray-400 uppercase">Qualification Match</p>
                <p class="text-3xl font-black text-white">Q{match_num}</p>
            </div>
            <div class="space-y-3">
                <div class="bg-primary/10 rounded p-3">
                    <p class="text-[10px] text-gray-400 uppercase mb-1">Your Alliance ({our_color.title()})</p>
                    <p class="text-sm text-white">{our_nums}</p>
                </div>
                <div class="text-center">
                    <span class="text-gray-500 font-bold text-xs">VS</span>
                </div>
                <div class="bg-white/5 rounded p-3">
                    <p class="text-[10px] text-gray-400 uppercase mb-1">Opponents</p>
                    <p class="text-sm {opp_color_class}">{opp_nums}</p>
                </div>
            </div>
        </div>
        '''
        
        container.innerHTML = html
    
    def render_previous_match(self, match, team_key):
        """Render previous match result"""
        container = document.getElementById('prev-match-content')
        
        if not match:
            container.innerHTML = '<div class="text-center text-gray-400 py-4"><p class="text-sm">No previous matches</p></div>'
            return
        
        match_num = match.get('match_number', '?')
        alliances = match.get('alliances', {})
        
        red_teams = alliances.get('red', {}).get('team_keys', [])
        blue_teams = alliances.get('blue', {}).get('team_keys', [])
        red_score = alliances.get('red', {}).get('score', 0)
        blue_score = alliances.get('blue', {}).get('score', 0)
        
        # Determine our alliance and result
        our_color = 'red' if team_key in red_teams else 'blue'
        our_score = red_score if our_color == 'red' else blue_score
        opp_score = blue_score if our_color == 'red' else red_score
        
        if our_score > opp_score:
            result = 'WIN'
            result_class = 'bg-primary/20 border-primary/50 text-primary'
        elif our_score < opp_score:
            result = 'LOSS'
            result_class = 'bg-red-500/20 border-red-500/50 text-red-400'
        else:
            result = 'TIE'
            result_class = 'bg-yellow-500/20 border-yellow-500/50 text-yellow-400'
        
        our_alliance = red_teams if our_color == 'red' else blue_teams
        our_nums = ', '.join([t.replace('frc', '') for t in our_alliance])
        
        html = f'''
        <div class="bg-black/40 rounded-lg p-4">
            <div class="flex items-center justify-between mb-4">
                <div>
                    <p class="text-[10px] text-gray-400 uppercase">Match {match_num}</p>
                    <p class="text-sm text-gray-300">{our_nums}</p>
                </div>
                <div class="px-4 py-2 rounded-lg border-2 {result_class}">
                    <p class="text-lg font-black">{result}</p>
                </div>
            </div>
            <div class="flex items-center justify-center gap-4">
                <div class="text-center">
                    <p class="text-[10px] text-gray-400 uppercase">Your Score</p>
                    <p class="text-3xl font-black text-white">{our_score}</p>
                </div>
                <span class="text-gray-500">-</span>
                <div class="text-center">
                    <p class="text-[10px] text-gray-400 uppercase">Opponent</p>
                    <p class="text-3xl font-black text-gray-400">{opp_score}</p>
                </div>
            </div>
        </div>
        '''
        
        container.innerHTML = html
    
    async def calculate_win_probability(self, match, team_key):
        """Calculate win probability for next match using Statbotics EPA"""
        container = document.getElementById('win-probability-content')
        
        if not match:
            container.innerHTML = '<div class="text-center text-gray-400 py-4"><p class="text-sm">No upcoming match to analyze</p></div>'
            return
        
        if not self.epa_data:
            await self.load_epa_data()
        
        if not self.epa_data:
            container.innerHTML = '<div class="text-center text-gray-400 py-4"><p class="text-sm">EPA data not available</p></div>'
            return
        
        alliances = match.get('alliances', {})
        red_teams = alliances.get('red', {}).get('team_keys', [])
        blue_teams = alliances.get('blue', {}).get('team_keys', [])
        
        # Calculate alliance EPAs using the lookup dict
        red_epa = 0
        blue_epa = 0
        
        for frc_key in red_teams:
            t_num = frc_key.replace('frc', '')
            record = self.epa_lookup.get(t_num)
            red_epa += get_epa_from_record(record)
        
        for frc_key in blue_teams:
            t_num = frc_key.replace('frc', '')
            record = self.epa_lookup.get(t_num)
            blue_epa += get_epa_from_record(record)
        
        # Determine our alliance
        our_color = 'red' if team_key in red_teams else 'blue'
        our_epa = red_epa if our_color == 'red' else blue_epa
        opp_epa = blue_epa if our_color == 'red' else red_epa
        
        # Calculate win probability
        if our_epa + opp_epa > 0:
            win_prob = our_epa / (our_epa + opp_epa) * 100
        else:
            win_prob = 50
        
        # Clamp between 20-80% for realism
        win_prob = max(20, min(80, win_prob))
        
        if win_prob >= 60:
            prob_class = 'text-primary'
            message = 'Strong advantage'
            bar_color = 'bg-primary'
        elif win_prob >= 50:
            prob_class = 'text-yellow-400'
            message = 'Slight advantage'
            bar_color = 'bg-yellow-400'
        else:
            prob_class = 'text-orange-400'
            message = 'Challenging match'
            bar_color = 'bg-orange-400'
        
        html = f'''
        <div class="text-center mb-4">
            <p class="{prob_class} text-6xl font-black mb-2">{win_prob:.0f}%</p>
            <p class="text-gray-400 text-sm">{message}</p>
        </div>
        
        <div class="bg-white/5 rounded-lg p-4 mb-4">
            <div class="flex justify-between mb-2">
                <span class="text-xs text-gray-400">Your Alliance EPA</span>
                <span class="text-xs text-white font-bold">{our_epa:.1f}</span>
            </div>
            <div class="flex justify-between">
                <span class="text-xs text-gray-400">Opponent EPA</span>
                <span class="text-xs text-white font-bold">{opp_epa:.1f}</span>
            </div>
        </div>
        
        <div class="h-3 w-full bg-white/5 rounded-full overflow-hidden">
            <div class="{bar_color} h-full rounded-full transition-all duration-1000" style="width: {win_prob}%"></div>
        </div>
        
        <p class="text-[10px] text-gray-500 mt-3 text-center">Probability based on Statbotics EPA</p>
        '''
        
        container.innerHTML = html


    async def load_schedule_view(self):
        """Load match schedule view"""
        if not self.matches_data:
            self.matches_data = await self.client.get_event_matches()
        
        if not self.epa_data and self.client.event_key:
            await self.load_epa_data()
        
        self.render_schedule(self.current_filter)
    
    async def load_epa_data(self):
        """
        Load Statbotics EPA for entire event (cached).
        Uses correct v3 endpoint: GET /team_events?event={event_key}
        Builds a lookup dict keyed by team number string for fast access.
        """
        if self.epa_data is not None:
            return self.epa_data

        event_key = self.client.event_key
        if not event_key:
            return None

        console.log(f"[Dashboard] Loading EPA for event: {event_key}")
        # Correct v3 endpoint: /team_events?event=EVENT_KEY
        result = await self.statbotics.get_event_teams(event_key)

        if not result:
            console.error("[Dashboard] EPA load failed or returned empty — Statbotics may not have data for this event yet")
            self.epa_data = []
            self.epa_lookup = {}
            return self.epa_data

        self.epa_data = result
        
        # Build lookup dict: team_number_str -> record
        self.epa_lookup = {}
        for record in self.epa_data:
            team_num = record.get('team')
            if team_num is not None:
                self.epa_lookup[str(team_num)] = record
        
        console.log(f"[Dashboard] Loaded EPA for {len(self.epa_data)} teams")
        return self.epa_data

    async def load_my_team_data(self):
        """Load Statbotics data for my team specifically"""
        team_num = self.client.team_number
        event_key = self.client.event_key

        if not team_num or not event_key:
            return

        console.log(f"[Dashboard] Loading my team {team_num} from Statbotics")
        # Correct v3 endpoint: /team_events?team=NUM&event=EVENT_KEY
        team_record = await self.statbotics.get_team_event(int(team_num), event_key)
        if team_record:
            self.epa_lookup[str(team_num)] = team_record
        
    def filter_schedule(self, event):
        """Filter schedule view"""
        btn = event.currentTarget
        filter_type = btn.getAttribute('data-filter')
        self.current_filter = filter_type
        
        # Update button styles
        filter_btns = document.querySelectorAll('.schedule-filter-btn')
        for b in filter_btns:
            b.classList.remove('bg-primary', 'text-background-dark')
            b.classList.add('bg-white/5', 'text-white')
        
        btn.classList.remove('bg-white/5', 'text-white')
        btn.classList.add('bg-primary', 'text-background-dark')
        
        self.render_schedule(filter_type)
    
    def render_schedule(self, filter_type):
        """Render match schedule based on filter"""
        if not self.matches_data:
            return
        
        qual_matches = [m for m in self.matches_data if m.get('comp_level') == 'qm']
        qual_matches.sort(key=lambda x: x.get('match_number', 0))
        
        # Apply filter
        if filter_type == 'upcoming':
            matches = [m for m in qual_matches if not m.get('actual_time')]
        elif filter_type == 'completed':
            matches = [m for m in qual_matches if m.get('actual_time')]
        elif filter_type == 'myteam':
            if self.client.team_number:
                team_key = f"frc{self.client.team_number}"
                matches = []
                for m in qual_matches:
                    alliances = m.get('alliances', {})
                    red_teams = alliances.get('red', {}).get('team_keys', [])
                    blue_teams = alliances.get('blue', {}).get('team_keys', [])
                    if team_key in red_teams or team_key in blue_teams:
                        matches.append(m)
            else:
                matches = []
        else:  # 'all'
            matches = qual_matches
        
        container = document.getElementById('schedule-matches')
        
        if not matches:
            container.innerHTML = '<div class="glass-card rounded-lg p-4 text-center text-gray-400"><p class="text-sm">No matches found</p></div>'
            return
        
        html = ''
        for match in matches:
            html += self.render_match_card(match)
        
        container.innerHTML = html
        
        # Add click handlers to match cards
        match_cards = document.querySelectorAll('.match-card')
        for card in match_cards:
            card.addEventListener('click', create_proxy(self.view_match_analysis))
    
    def render_match_card(self, match):
        """Render a single match card"""
        match_num = match.get('match_number', '?')
        match_key = match.get('key', '')
        
        alliances = match.get('alliances', {})
        red_teams = alliances.get('red', {}).get('team_keys', [])
        blue_teams = alliances.get('blue', {}).get('team_keys', [])
        
        red_nums = ', '.join([t.replace('frc', '') for t in red_teams])
        blue_nums = ', '.join([t.replace('frc', '') for t in blue_teams])
        
        is_completed = match.get('actual_time') is not None
        
        if is_completed:
            red_score = alliances.get('red', {}).get('score', 0)
            blue_score = alliances.get('blue', {}).get('score', 0)
            
            red_class = 'text-primary font-bold' if red_score > blue_score else 'text-gray-400'
            blue_class = 'text-primary font-bold' if blue_score > red_score else 'text-gray-400'
            
            scores_html = f'''
            <div class="flex gap-4 text-center">
                <div>
                    <p class="text-xs text-gray-400 uppercase">Red</p>
                    <p class="text-2xl font-black {red_class}">{red_score}</p>
                </div>
                <span class="text-gray-500 self-center">-</span>
                <div>
                    <p class="text-xs text-gray-400 uppercase">Blue</p>
                    <p class="text-2xl font-black {blue_class}">{blue_score}</p>
                </div>
            </div>
            '''
        else:
            scores_html = '<p class="text-xs text-gray-500 uppercase">Not Played</p>'
        
        return f'''
        <div class="match-card glass-card rounded-lg p-4 cursor-pointer hover:border-primary/30 border border-transparent transition-colors" data-match-key="{match_key}">
            <div class="flex items-center justify-between">
                <div class="flex items-center gap-4">
                    <div class="text-center">
                        <p class="text-[10px] text-gray-400 uppercase">Match</p>
                        <p class="text-xl font-black text-white leading-none">Q{match_num}</p>
                    </div>
                    <div class="flex-1">
                        <div class="mb-2">
                            <p class="text-[10px] text-red-400 uppercase font-bold">Red</p>
                            <p class="text-sm text-white">{red_nums}</p>
                        </div>
                        <div>
                            <p class="text-[10px] text-blue-400 uppercase font-bold">Blue</p>
                            <p class="text-sm text-white">{blue_nums}</p>
                        </div>
                    </div>
                </div>
                <div class="flex items-center gap-4">
                    {scores_html}
                    <span class="material-symbols-outlined text-primary">arrow_forward_ios</span>
                </div>
            </div>
        </div>
        '''
    
    async def view_match_analysis(self, event):
        """View detailed match analysis"""
        card = event.target.closest('.match-card')
        if not card:
            return
        
        match_key = card.getAttribute('data-match-key')
        
        if not match_key:
            return
        
        # Find the match
        match = None
        for m in self.matches_data:
            if m.get('key') == match_key:
                match = m
                break
        
        if not match:
            return
        
        # Switch to analysis view
        views = document.querySelectorAll('.view-container')
        for view in views:
            view.classList.remove('active')
        
        analysis_view = document.getElementById('view-match-analysis')
        if analysis_view:
            analysis_view.classList.add('active')
        
        await self.render_match_analysis(match)
    
    async def render_match_analysis(self, match):
        """Render detailed match analysis using Statbotics EPA"""
        container = document.getElementById('match-analysis-content')
        
        if not self.epa_data:
            await self.load_epa_data()
        
        match_num = match.get('match_number', '?')
        alliances = match.get('alliances', {})
        
        red_teams = alliances.get('red', {}).get('team_keys', [])
        blue_teams = alliances.get('blue', {}).get('team_keys', [])
        
        red_epa_total = 0
        blue_epa_total = 0
        red_norm_total = 0
        blue_norm_total = 0
        
        red_team_epas = []
        blue_team_epas = []
        
        # Use the lookup dict for fast EPA access
        for frc_key in red_teams:
            t_num = frc_key.replace('frc', '')
            record = self.epa_lookup.get(t_num)
            epa = get_epa_from_record(record)
            norm = get_norm_epa_from_record(record)
            red_epa_total += epa
            red_norm_total += norm
            red_team_epas.append((frc_key, epa, norm))
        
        for frc_key in blue_teams:
            t_num = frc_key.replace('frc', '')
            record = self.epa_lookup.get(t_num)
            epa = get_epa_from_record(record)
            norm = get_norm_epa_from_record(record)
            blue_epa_total += epa
            blue_norm_total += norm
            blue_team_epas.append((frc_key, epa, norm))
        
        # Calculate win probability
        if red_epa_total + blue_epa_total > 0:
            red_win_prob = red_epa_total / (red_epa_total + blue_epa_total) * 100
        else:
            red_win_prob = 50
        
        blue_win_prob = 100 - red_win_prob
        
        winner = 'RED' if red_win_prob > 50 else 'BLUE'
        winner_class = 'text-red-400' if winner == 'RED' else 'text-blue-400'
        
        red_expected_score = red_epa_total if red_epa_total > 0 else 0
        blue_expected_score = blue_epa_total if blue_epa_total > 0 else 0
        
        # Build team detail HTML
        red_teams_html = ''
        for team_key, epa, norm in red_team_epas:
            team_num = team_key.replace('frc', '')
            epa_str = f"{epa:.1f}" if epa else "N/A"
            norm_str = f"{norm:.1f}" if norm else "N/A"
            red_teams_html += f'''
            <div class="flex justify-between items-center p-2 bg-black/20 rounded">
                <span class="text-white font-bold">{team_num}</span>
                <div class="text-right">
                    <p class="text-xs text-gray-400">EPA: <span class="text-white">{epa_str}</span></p>
                    <p class="text-[10px] text-gray-500">Norm: {norm_str}</p>
                </div>
            </div>
            '''
        
        blue_teams_html = ''
        for team_key, epa, norm in blue_team_epas:
            team_num = team_key.replace('frc', '')
            epa_str = f"{epa:.1f}" if epa else "N/A"
            norm_str = f"{norm:.1f}" if norm else "N/A"
            blue_teams_html += f'''
            <div class="flex justify-between items-center p-2 bg-black/20 rounded">
                <span class="text-white font-bold">{team_num}</span>
                <div class="text-right">
                    <p class="text-xs text-gray-400">EPA: <span class="text-white">{epa_str}</span></p>
                    <p class="text-[10px] text-gray-500">Norm: {norm_str}</p>
                </div>
            </div>
            '''
        
        html = f'''
        <section class="glass-card rounded-xl p-6">
            <div class="text-center mb-6">
                <p class="text-xs text-gray-400 uppercase">Qualification Match</p>
                <h2 class="text-4xl font-black text-white mb-2">Q{match_num}</h2>
                <p class="text-sm text-gray-400">Powered by Statbotics EPA</p>
            </div>
            
            <div class="text-center mb-6">
                <p class="text-sm text-gray-400 mb-2">Predicted Winner</p>
                <p class="{winner_class} text-6xl font-black">{winner}</p>
            </div>
            
            <div class="grid grid-cols-2 gap-4 mb-6">
                <div class="text-center">
                    <p class="text-xs text-gray-400 uppercase">Red Win %</p>
                    <p class="text-3xl font-bold text-red-400">{red_win_prob:.1f}%</p>
                </div>
                <div class="text-center">
                    <p class="text-xs text-gray-400 uppercase">Blue Win %</p>
                    <p class="text-3xl font-bold text-blue-400">{blue_win_prob:.1f}%</p>
                </div>
            </div>
            
            <div class="h-4 w-full bg-white/5 rounded-full overflow-hidden mb-6">
                <div class="h-full bg-gradient-to-r from-red-500 to-blue-500 rounded-full transition-all duration-1000" style="width: {red_win_prob}%"></div>
            </div>
        </section>
        
        <section class="bg-red-500/10 border-2 border-red-500/30 rounded-xl p-5">
            <h3 class="text-red-400 text-sm font-bold uppercase tracking-widest mb-4">Red Alliance</h3>
            <div class="space-y-2 mb-4">
                {red_teams_html}
            </div>
            <div class="bg-black/40 rounded-lg p-3">
                <div class="grid grid-cols-2 gap-4 text-sm">
                    <div>
                        <p class="text-gray-400">Total EPA</p>
                        <p class="text-white font-bold text-lg">{red_epa_total:.1f}</p>
                    </div>
                    <div>
                        <p class="text-gray-400">Expected Score</p>
                        <p class="text-white font-bold text-lg">{red_expected_score:.0f}</p>
                    </div>
                </div>
            </div>
        </section>
        
        <section class="bg-blue-500/10 border-2 border-blue-500/30 rounded-xl p-5">
            <h3 class="text-blue-400 text-sm font-bold uppercase tracking-widest mb-4">Blue Alliance</h3>
            <div class="space-y-2 mb-4">
                {blue_teams_html}
            </div>
            <div class="bg-black/40 rounded-lg p-3">
                <div class="grid grid-cols-2 gap-4 text-sm">
                    <div>
                        <p class="text-gray-400">Total EPA</p>
                        <p class="text-white font-bold text-lg">{blue_epa_total:.1f}</p>
                    </div>
                    <div>
                        <p class="text-gray-400">Expected Score</p>
                        <p class="text-white font-bold text-lg">{blue_expected_score:.0f}</p>
                    </div>
                </div>
            </div>
        </section>
        
        <section class="glass-card rounded-xl p-5">
            <h3 class="text-white text-xs font-bold uppercase tracking-widest mb-3">About EPA</h3>
            <p class="text-xs text-gray-400 mb-2">
                <span class="text-primary font-bold">EPA (Expected Points Added)</span> measures how many points a team is expected to contribute to their alliance's score.
            </p>
            <p class="text-xs text-gray-400">
                <span class="text-primary font-bold">Normalized EPA</span> is adjusted for seasonal strength, making it comparable across different years and events.
            </p>
        </section>
        '''
        
        container.innerHTML = html
    
    def switch_epa_type(self, event):
        """Switch between EPA and Unitless EPA"""
        btn = event.currentTarget
        epa_type = btn.getAttribute('data-type')
        self.epa_type = epa_type
        
        # Update button styles
        epa_btns = document.querySelectorAll('.epa-type-btn')
        for b in epa_btns:
            b.classList.remove('bg-primary', 'text-background-dark')
            b.classList.add('bg-white/5', 'text-white')
        
        btn.classList.remove('bg-white/5', 'text-white')
        btn.classList.add('bg-primary', 'text-background-dark')
    
    async def calculate_custom_matchup(self, event):
        """Calculate win probability for custom alliance matchup"""
        red_teams = [
            document.getElementById('red-team-1').value.strip(),
            document.getElementById('red-team-2').value.strip(),
            document.getElementById('red-team-3').value.strip()
        ]
        
        blue_teams = [
            document.getElementById('blue-team-1').value.strip(),
            document.getElementById('blue-team-2').value.strip(),
            document.getElementById('blue-team-3').value.strip()
        ]
        
        red_teams = [t for t in red_teams if t]
        blue_teams = [t for t in blue_teams if t]
        
        if len(red_teams) == 0 or len(blue_teams) == 0:
            return
        
        if not self.epa_data:
            await self.load_epa_data()
        
        if not self.epa_data:
            return
        
        # Calculate EPA totals using lookup dict
        red_epa = 0
        blue_epa = 0
        red_norm_epa = 0
        blue_norm_epa = 0
        
        for team_num in red_teams:
            record = self.epa_lookup.get(team_num)
            red_epa += get_epa_from_record(record)
            red_norm_epa += get_norm_epa_from_record(record)
        
        for team_num in blue_teams:
            record = self.epa_lookup.get(team_num)
            blue_epa += get_epa_from_record(record)
            blue_norm_epa += get_norm_epa_from_record(record)
        
        # Use selected EPA type
        if self.epa_type == 'unitless':
            red_value = red_norm_epa
            blue_value = blue_norm_epa
        else:
            red_value = red_epa
            blue_value = blue_epa
        
        # Calculate win probability
        if red_value + blue_value > 0:
            red_win_prob = red_value / (red_value + blue_value) * 100
        else:
            red_win_prob = 50
        
        blue_win_prob = 100 - red_win_prob
        
        winner = 'RED' if red_win_prob > 50 else 'BLUE'
        winner_class = 'text-red-400' if winner == 'RED' else 'text-blue-400'
        
        # Show results
        prediction_section = document.getElementById('builder-prediction')
        prediction_section.classList.remove('hidden')
        
        document.getElementById('winner-display').textContent = winner
        document.getElementById('winner-display').className = f'text-6xl font-black mb-2 {winner_class}'
        
        document.getElementById('red-win-prob').textContent = f'{red_win_prob:.1f}%'
        document.getElementById('blue-win-prob').textContent = f'{blue_win_prob:.1f}%'
        
        display_red = red_norm_epa if self.epa_type == 'unitless' else red_epa
        display_blue = blue_norm_epa if self.epa_type == 'unitless' else blue_epa
        
        document.getElementById('builder-red-epa').textContent = f'{display_red:.1f}'
        document.getElementById('builder-blue-epa').textContent = f'{display_blue:.1f}'
        
        document.getElementById('builder-red-score').textContent = f'{red_epa:.0f}' if red_epa > 0 else '--'
        document.getElementById('builder-blue-score').textContent = f'{blue_epa:.0f}' if blue_epa > 0 else '--'
        
        # Update progress bar
        bar = document.getElementById('builder-prob-bar')
        bar.style.width = f'{red_win_prob}%'
        
        # Show alliance stats
        document.getElementById('red-alliance-stats').classList.remove('hidden')
        document.getElementById('blue-alliance-stats').classList.remove('hidden')
        
        document.getElementById('red-total-epa').textContent = f'{display_red:.1f}'
        document.getElementById('blue-total-epa').textContent = f'{display_blue:.1f}'


# Initialize dashboard when page loads
dashboard = Dashboard()