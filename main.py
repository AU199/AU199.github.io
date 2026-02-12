import json
import pyodide_http
from pyodide.ffi import create_proxy, to_js
from js import document, localStorage, fetch, console,Object

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
            # Python dict
            headers_dict = {
                "X-TBA-Auth-Key": self.api_key.strip()
            }

            # Convert Python dict → JS object
            headers_js = to_js(headers_dict)

            console.log(f"Making request to: {url}")
            console.log(f"API Key length: {len(self.api_key.strip())}")

            # JS options object
            options = Object.fromEntries(to_js([
                ["method", "GET"],
                ["headers", headers_js]
            ]))

            response = await fetch(url, options)

            console.log(f"Response status: {response.status}")

            if response.status == 200:
                data = await response.json()
                return data.to_py()   # convert JS → Python
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
        
        # Settings button
        settings_btn = document.getElementById('settings-btn')
        if settings_btn:
            settings_btn.addEventListener('click', create_proxy(self.open_settings))
        
        # Close settings
        close_btn = document.getElementById('close-settings')
        if close_btn:
            close_btn.addEventListener('click', create_proxy(self.close_settings))
        
        # Save settings
        save_btn = document.getElementById('save-settings')
        if save_btn:
            save_btn.addEventListener('click', create_proxy(self.save_settings))
    
    def check_initial_setup(self):
        """Check if initial setup is needed"""
        if self.client.api_key and self.client.event_key:
            # Already set up, hide wizard and load data
            wizard = document.getElementById('setup-wizard')
            if wizard:
                wizard.style.display = 'none'
            self.update_sync_status(True)
            # Create task to load data
            import asyncio
            asyncio.create_task(self.load_all_data())
        else:
            # Show wizard
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
        
        # Show validating message
        error_div.innerHTML = '<p class="text-yellow-400 text-xs font-bold">⏳ Validating API key...</p>'
        error_div.classList.remove('hidden')
        error_div.className = 'mt-2 p-3 bg-yellow-500/10 border border-yellow-500/30 rounded-lg'
        
        # Test API key by making a simple request
        temp_client = TBAClient()
        temp_client.api_key = api_key
        
        try:
            # Test with a simple API call
            test_result = await temp_client.make_request('status')
            
            if test_result is None:
                error_div.innerHTML = '<p class="text-red-400 text-xs font-bold">⚠️ Invalid API key. Please check and try again.</p>'
                error_div.className = 'mt-2 p-3 bg-red-500/10 border border-red-500/30 rounded-lg'
                return
            
            # API key is valid
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
        
        # Show validating message
        error_div.innerHTML = '<p class="text-yellow-400 text-xs font-bold">⏳ Validating event key...</p>'
        error_div.classList.remove('hidden')
        error_div.className = 'mt-2 p-3 bg-yellow-500/10 border border-yellow-500/30 rounded-lg'
        
        # Validate event key
        temp_client = TBAClient()
        temp_client.api_key = api_key
        temp_client.event_key = event_key
        
        try:
            event_data = await temp_client.get_event_info()
            
            if event_data is None:
                error_div.innerHTML = '<p class="text-red-400 text-xs font-bold">⚠️ Event not found. Check the event key and try again.</p>'
                error_div.className = 'mt-2 p-3 bg-red-500/10 border border-red-500/30 rounded-lg'
                return
            
            # Both are valid, save settings
            error_div.classList.add('hidden')
            
            # Save settings
            self.client.save_settings(api_key, event_key, team_number)
            
            # Also update settings modal inputs
            document.getElementById('api-key-input').value = api_key
            document.getElementById('event-key-input').value = event_key
            document.getElementById('team-number-input').value = team_number
            
            # Hide wizard
            document.getElementById('setup-wizard').style.display = 'none'
            
            # Update sync status
            self.update_sync_status(True)
            
            # Show loading and then load data
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
        
        # Close modal
        modal = document.getElementById('settings-modal')
        modal.classList.add('hidden')
        modal.style.display = 'none'
        
        # Update sync status
        self.update_sync_status(True)
        
        # Load data
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
            # Load event info
            await self.load_event_info()
            
            # Load matches and calculate stats
            await self.load_matches()
            
            # Load rankings/leaderboard
            await self.load_rankings()
            
            # Load my team data if set
            if self.client.team_number:
                await self.load_my_team()
            
            self.hide_loading()
            
        except Exception as e:
            console.error(f"Error loading data: {str(e)}")
            self.hide_loading()
    
    async def load_event_info(self):
        """Load and display event information"""
        event_data = await self.client.get_event_info()
        if event_data:
            event_name = event_data.get('name', 'Unknown Event')
            # Truncate if too long
            if len(event_name) > 30:
                event_name = event_name[:27] + '...'
            document.getElementById('event-name').textContent = event_name
    
    async def load_matches(self):
        """Load and display match data"""
        matches = await self.client.get_event_matches()
        
        if not matches:
            return
        
        # Filter qualification matches
        qual_matches = [m for m in matches if m.get('comp_level') == 'qm']
        
        # Calculate statistics
        total_matches = len(qual_matches)
        completed_matches = len([m for m in qual_matches if m.get('actual_time')])
        
        # Calculate average score
        scores = []
        for match in qual_matches:
            if match.get('alliances'):
                red_score = match['alliances'].get('red', {}).get('score', 0)
                blue_score = match['alliances'].get('blue', {}).get('score', 0)
                if red_score and blue_score:
                    scores.append(red_score)
                    scores.append(blue_score)
        
        avg_score = sum(scores) / len(scores) if scores else 0
        
        # Update UI
        document.getElementById('avg-score').textContent = f"{avg_score:.1f}"
        document.getElementById('total-matches').textContent = str(total_matches)
        
        # Update progress
        if total_matches > 0:
            progress = (completed_matches / total_matches) * 100
            document.getElementById('progress-bar').style.width = f"{progress}%"
            document.getElementById('progress-text').textContent = f"{int(progress)}% of qualification matches completed"
            
            remaining = total_matches - completed_matches
            document.getElementById('event-status').textContent = f"Event in progress • {remaining} matches remaining"
        
        # Load upcoming matches
        await self.load_upcoming_matches(qual_matches)
    
    async def load_upcoming_matches(self, matches):
        """Load upcoming matches"""
        # Get unplayed matches
        upcoming = [m for m in matches if not m.get('actual_time')]
        upcoming.sort(key=lambda x: x.get('match_number', 0))
        
        container = document.getElementById('upcoming-matches')
        
        if not upcoming:
            container.innerHTML = '<div class="text-center text-gray-400 py-4"><p class="text-sm">No upcoming matches</p></div>'
            return
        
        # Show first 3 upcoming matches
        html = ''
        for match in upcoming[:3]:
            match_num = match.get('match_number', '?')
            
            red_teams = match.get('alliances', {}).get('red', {}).get('team_keys', [])
            blue_teams = match.get('alliances', {}).get('blue', {}).get('team_keys', [])
            
            # Extract team numbers (remove 'frc' prefix)
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
        rankings_data = await self.client.get_event_rankings()
        oprs_data = await self.client.get_event_oprs()
        
        if not rankings_data or not rankings_data.get('rankings'):
            return
        
        rankings = rankings_data['rankings']
        oprs = oprs_data.get('oprs', {}) if oprs_data else {}
        
        # Update total teams
        document.getElementById('total-teams').textContent = str(len(rankings))
        
        # Show top 10 teams
        container = document.getElementById('leaderboard')
        html = ''
        
        for i, team_data in enumerate(rankings[:10]):
            rank = team_data.get('rank', i + 1)
            team_key = team_data.get('team_key', '')
            team_num = team_key.replace('frc', '')
            
            # Get OPR if available
            opr = oprs.get(team_key, 0)
            opr_text = f"{opr:.1f} OPR" if opr else "N/A"
            
            # Record
            record = team_data.get('record', {})
            wins = record.get('wins', 0)
            losses = record.get('losses', 0)
            ties = record.get('ties', 0)
            
            # Highlight top 3
            border_class = 'border-l-primary' if rank <= 3 else 'border-l-white/10'
            text_color = 'text-primary' if rank <= 3 else 'text-white'
            
            # Is this a top team? (just checking if rank 1 for "Pro" badge)
            badge = '<span class="bg-primary/10 text-primary text-[10px] px-1.5 py-0.5 rounded font-bold uppercase">Pro</span>' if rank == 1 else ''
            
            html += f'''
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
                        <div class="h-4 w-1 bg-{text_color.split('-')[1]}/60"></div>
                        <div class="h-3 w-1 bg-{text_color.split('-')[1]}/40"></div>
                        <div class="h-5 w-1 bg-{text_color.split('-')[1]}/80"></div>
                        <div class="h-4 w-1 bg-{text_color.split('-')[1]}/50"></div>
                    </div>
                </div>
            </div>
            '''
        
        container.innerHTML = html
    
    async def load_my_team(self):
        """Load my team statistics"""
        team_key = f"frc{self.client.team_number}"
        
        # Get team status
        status = await self.client.get_team_status(team_key)
        rankings_data = await self.client.get_event_rankings()
        oprs_data = await self.client.get_event_oprs()
        
        if not status:
            return
        
        # Show section
        section = document.getElementById('my-team-section')
        section.classList.remove('hidden')
        
        # Update team number
        document.getElementById('my-team-number').textContent = self.client.team_number
        
        # Get rank
        qual = status.get('qual', {})
        ranking = qual.get('ranking', {})
        rank = ranking.get('rank', '--')
        
        document.getElementById('my-team-rank').textContent = f"#{rank}"
        
        # Get record
        record = ranking.get('record', {})
        wins = record.get('wins', 0)
        losses = record.get('losses', 0)
        ties = record.get('ties', 0)
        
        document.getElementById('my-team-record').textContent = f"{wins}-{losses}-{ties}"
        
        # Calculate average score from matches
        matches = await self.client.get_event_matches()
        if matches:
            team_scores = []
            for match in matches:
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
        if oprs_data:
            opr = oprs_data.get('oprs', {}).get(team_key, 0)
            document.getElementById('my-team-opr').textContent = f"{opr:.1f}"


# Initialize dashboard when page loads
dashboard = Dashboard()