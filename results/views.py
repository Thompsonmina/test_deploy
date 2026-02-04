"""
Django Views for Election Results
=================================
This file contains all the views to handle the three questions:
1. Display results for individual polling units
2. Display summed results for all polling units under an LGA
3. Store results for ALL parties for a new polling unit
"""

from django.shortcuts import render, redirect, get_object_or_404
from django.http import JsonResponse
from django.contrib import messages
from django.db.models import Sum
from django.utils import timezone
from .models import State, Lga, Ward, PollingUnit, Party, AnnouncedPuResults


def index(request):
    """Home page - show navigation to all features."""
    return render(request, 'results/index.html')


# =============================================================================
# QUESTION 1: Display results for any individual polling unit
# =============================================================================

def polling_unit_results(request):
    """
    Question 1: Display the result for any individual polling unit.
    User can select a polling unit from Delta State (state_id = 25).
    """
    # Get all LGAs in Delta State (state_id = 25)
    lgas = Lga.objects.filter(state_id=25).order_by('lga_name')
    
    # Get all polling units in Delta State with their LGA and Ward names
    # Using raw SQL for the join since we're not using ForeignKey relations
    polling_units = PollingUnit.objects.raw('''
        SELECT pu.uniqueid, pu.polling_unit_name, pu.polling_unit_number, 
               l.lga_name, w.ward_name
        FROM polling_unit pu
        JOIN lga l ON pu.lga_id = l.lga_id AND l.state_id = 25
        LEFT JOIN ward w ON pu.ward_id = w.ward_id AND pu.lga_id = w.lga_id
        WHERE pu.polling_unit_name IS NOT NULL AND pu.polling_unit_name != ''
        ORDER BY l.lga_name, pu.polling_unit_name
    ''')
    
    results = None
    selected_pu = None
    total_votes = 0
    
    # Handle form submission or URL parameter
    pu_id = request.POST.get('polling_unit') or request.GET.get('pu_id')
    
    if pu_id:
        try:
            # Get polling unit details
            selected_pu = PollingUnit.objects.raw('''
                SELECT pu.*, l.lga_name, w.ward_name
                FROM polling_unit pu
                JOIN lga l ON pu.lga_id = l.lga_id
                LEFT JOIN ward w ON pu.ward_id = w.ward_id AND pu.lga_id = w.lga_id
                WHERE pu.uniqueid = %s
            ''', [pu_id])[0]
            
            # Get results for this polling unit
            results = AnnouncedPuResults.objects.filter(
                polling_unit_uniqueid=str(pu_id)
            ).order_by('-party_score')
            
            # Calculate total votes
            total_votes = sum(r.party_score for r in results)
            
        except (IndexError, PollingUnit.DoesNotExist):
            messages.error(request, 'Polling unit not found.')
    
    context = {
        'lgas': lgas,
        'polling_units': list(polling_units),
        'results': results,
        'selected_pu': selected_pu,
        'total_votes': total_votes,
    }
    return render(request, 'results/polling_unit_results.html', context)


# =============================================================================
# QUESTION 2: Display summed total results for all polling units under an LGA
# =============================================================================

def lga_results(request):
    """
    Question 2: Display the summed total result of all polling units under 
    any particular local government.
    
    NOTE: As per instructions, we do NOT use announced_lga_results table.
    Instead, we sum up results from announced_pu_results for all polling 
    units in the selected LGA.
    """
    # Get all LGAs in Delta State (state_id = 25)
    lgas = Lga.objects.filter(state_id=25).order_by('lga_name')
    
    results = None
    selected_lga = None
    total_votes = 0
    polling_unit_count = 0
    
    # Handle form submission or URL parameter
    lga_uniqueid = request.POST.get('lga') or request.GET.get('lga_id')
    
    if lga_uniqueid:
        try:
            # Get LGA details
            selected_lga = Lga.objects.get(uniqueid=lga_uniqueid)
            lga_id = selected_lga.lga_id
            
            # Count polling units in this LGA
            polling_unit_count = PollingUnit.objects.filter(lga_id=lga_id).count()
            
            # Sum results from all polling units in this LGA
            # This joins polling_unit with announced_pu_results
            results = AnnouncedPuResults.objects.raw('''
                SELECT 
                    1 as result_id,
                    apr.party_abbreviation,
                    SUM(apr.party_score) as total_score
                FROM announced_pu_results apr
                JOIN polling_unit pu ON apr.polling_unit_uniqueid = CAST(pu.uniqueid AS TEXT)
                WHERE pu.lga_id = %s
                GROUP BY apr.party_abbreviation
                ORDER BY total_score DESC
            ''', [lga_id])
            
            # Convert to list and calculate total
            results = list(results)
            total_votes = sum(r.total_score for r in results) if results else 0
            
        except Lga.DoesNotExist:
            messages.error(request, 'LGA not found.')
    
    context = {
        'lgas': lgas,
        'results': results,
        'selected_lga': selected_lga,
        'total_votes': total_votes,
        'polling_unit_count': polling_unit_count,
    }
    return render(request, 'results/lga_results.html', context)


# =============================================================================
# QUESTION 3: Store results for ALL parties for a new polling unit
# =============================================================================

def add_results(request):
    """
    Question 3: Create a page to store results for ALL parties for a new polling unit.
    Uses chained combo boxes: LGA -> Ward -> Enter Results
    """
    # Get all parties
    parties = Party.objects.all().order_by('partyname')
    
    # Get all LGAs in Delta State
    lgas = Lga.objects.filter(state_id=25).order_by('lga_name')
    
    if request.method == 'POST':
        # Get form data
        lga_uniqueid = request.POST.get('lga_id')
        ward_id = request.POST.get('ward_id')
        pu_name = request.POST.get('pu_name', '').strip()
        pu_number = request.POST.get('pu_number', '').strip()
        entered_by = request.POST.get('entered_by', 'Anonymous').strip()
        
        # Validation
        if not lga_uniqueid or not ward_id or not pu_name:
            messages.error(request, 'Please fill in all required fields (LGA, Ward, and Polling Unit Name)')
        else:
            try:
                # Get the actual lga_id from the uniqueid
                lga = Lga.objects.get(uniqueid=lga_uniqueid)
                actual_lga_id = lga.lga_id
                
                # Create new polling unit
                new_pu = PollingUnit.objects.create(
                    polling_unit_id=0,
                    ward_id=int(ward_id),
                    lga_id=actual_lga_id,
                    polling_unit_number=pu_number or None,
                    polling_unit_name=pu_name,
                    entered_by_user=entered_by,
                    date_entered=timezone.now(),
                    user_ip_address=get_client_ip(request)
                )
                
                # Store results for ALL parties
                results_added = 0
                for party in parties:
                    party_abbr = party.partyid
                    score_key = f'party_{party_abbr}'
                    score = request.POST.get(score_key, 0)
                    
                    try:
                        score = int(score) if score else 0
                    except ValueError:
                        score = 0
                    
                    # Create result for this party
                    AnnouncedPuResults.objects.create(
                        polling_unit_uniqueid=str(new_pu.uniqueid),
                        party_abbreviation=party_abbr,
                        party_score=score,
                        entered_by_user=entered_by,
                        date_entered=timezone.now(),
                        user_ip_address=get_client_ip(request)
                    )
                    results_added += 1
                
                messages.success(
                    request, 
                    f'Successfully added polling unit "{pu_name}" with results for {results_added} parties!'
                )
                
                # Redirect to view the new polling unit's results
                return redirect(f'/polling-unit-results/?pu_id={new_pu.uniqueid}')
                
            except Lga.DoesNotExist:
                messages.error(request, 'Invalid LGA selected.')
            except Exception as e:
                messages.error(request, f'Error adding results: {str(e)}')
    
    context = {
        'lgas': lgas,
        'parties': parties,
    }
    return render(request, 'results/add_results.html', context)


# =============================================================================
# API Endpoints for chained dropdowns (AJAX)
# =============================================================================

def api_get_wards(request, lga_uniqueid):
    """API endpoint to get wards for a specific LGA."""
    try:
        lga = Lga.objects.get(uniqueid=lga_uniqueid)
        wards = Ward.objects.filter(lga_id=lga.lga_id).order_by('ward_name')
        
        data = [
            {
                'uniqueid': w.uniqueid,
                'ward_id': w.ward_id,
                'ward_name': w.ward_name
            }
            for w in wards
        ]
        return JsonResponse(data, safe=False)
    
    except Lga.DoesNotExist:
        return JsonResponse([], safe=False)


def api_get_polling_units(request, lga_uniqueid):
    """API endpoint to get polling units for a specific LGA."""
    try:
        lga = Lga.objects.get(uniqueid=lga_uniqueid)
        
        polling_units = PollingUnit.objects.raw('''
            SELECT pu.uniqueid, pu.polling_unit_name, pu.polling_unit_number, w.ward_name
            FROM polling_unit pu
            LEFT JOIN ward w ON pu.ward_id = w.ward_id AND pu.lga_id = w.lga_id
            WHERE pu.lga_id = %s AND pu.polling_unit_name IS NOT NULL AND pu.polling_unit_name != ''
            ORDER BY w.ward_name, pu.polling_unit_name
        ''', [lga.lga_id])
        
        data = [
            {
                'uniqueid': pu.uniqueid,
                'name': pu.polling_unit_name,
                'number': pu.polling_unit_number,
                'ward': pu.ward_name
            }
            for pu in polling_units
        ]
        return JsonResponse(data, safe=False)
    
    except Lga.DoesNotExist:
        return JsonResponse([], safe=False)


# =============================================================================
# Helper Functions
# =============================================================================

def get_client_ip(request):
    """Get the client's IP address from the request."""
    x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
    if x_forwarded_for:
        ip = x_forwarded_for.split(',')[0]
    else:
        ip = request.META.get('REMOTE_ADDR')
    return ip or '127.0.0.1'
