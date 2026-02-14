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


class Dashboard:
    """Main dashboard controller"""
    
    def __init__(self):
        self.client = TBAClient()
        self.current_view = 'scout'
        self.matches_data = None
        self.rankings_data = None
        self.oprs_data = None
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
        """Load all data from TBA"""
        self.show_loading("Loading event data...")
        
        try:
            await self.load_event_info()
            await self.load_matches()
            await self.load_rankings()
            
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
        
        # Load team status
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
        
        # Calculate average score
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
        
        # Get OPR
        if not self.oprs_data:
            self.oprs_data = await self.client.get_event_oprs()
        
        if self.oprs_data:
            opr = self.oprs_data.get('oprs', {}).get(team_key, 0)
            document.getElementById('my-team-opr').textContent = f"{opr:.1f}"
        
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
        self.calculate_win_probability(next_match, team_key)
    
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
    
    def calculate_win_probability(self, match, team_key):
        """Calculate and display win probability for next match"""
        container = document.getElementById('win-probability-content')
        
        if not match or not self.oprs_data:
            container.innerHTML = '<div class="text-center text-gray-400 py-4"><p class="text-sm">No upcoming match to analyze</p></div>'
            return
        
        oprs = self.oprs_data.get('oprs', {})
        
        alliances = match.get('alliances', {})
        red_teams = alliances.get('red', {}).get('team_keys', [])
        blue_teams = alliances.get('blue', {}).get('team_keys', [])
        
        # Calculate alliance OPRs
        red_opr = sum([oprs.get(t, 0) for t in red_teams])
        blue_opr = sum([oprs.get(t, 0) for t in blue_teams])
        
        # Determine our alliance
        our_color = 'red' if team_key in red_teams else 'blue'
        our_opr = red_opr if our_color == 'red' else blue_opr
        opp_opr = blue_opr if our_color == 'red' else red_opr
        
        # Simple win probability based on OPR difference
        # Using logistic function for probability
        if our_opr + opp_opr > 0:
            win_prob = our_opr / (our_opr + opp_opr) * 100
        else:
            win_prob = 50
        
        # Clamp between 20-80% for realism
        win_prob = max(20, min(80, win_prob))
        
        # Determine color and message
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
                <span class="text-xs text-gray-400">Your Alliance OPR</span>
                <span class="text-xs text-white font-bold">{our_opr:.1f}</span>
            </div>
            <div class="flex justify-between">
                <span class="text-xs text-gray-400">Opponent OPR</span>
                <span class="text-xs text-white font-bold">{opp_opr:.1f}</span>
            </div>
        </div>
        
        <div class="h-3 w-full bg-white/5 rounded-full overflow-hidden">
            <div class="{bar_color} h-full rounded-full transition-all duration-1000" style="width: {win_prob}%"></div>
        </div>
        
        <p class="text-[10px] text-gray-500 mt-3 text-center">Probability based on alliance OPR comparison</p>
        '''
        
        container.innerHTML = html


# Initialize dashboard when page loads
dashboard = Dashboard()