import json
from django.views.generic import TemplateView
from django.http import Http404
from django.shortcuts import render,redirect, get_object_or_404

from base import mods
from census.models import Census
from voting.models import Voting
from store.models import Vote

class VisualizerView(TemplateView):
    template_name = 'visualizer/visualizer.html'


    def get_template_names(self):

        if self.request.user_agent.is_mobile:
            self.template_name = 'visualizer/visualizer_mobile.html'
        else:
            self.template_name = 'visualizer/visualizer.html'

        
        return [self.template_name]
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        vid = kwargs.get('voting_id', 0)

        try:
            r = mods.get('voting', params={'id': vid})
            
            context['voting'] = json.dumps(r[0])
            context['is_mobile'] = self.request.user_agent.is_mobile

            token = self.request.session.get('auth-token', '')

            v = r[0]
            v_id = v['id']

            voting = get_object_or_404(Voting, id=vid)

            if voting.end_date is None:
                voting.live_tally(token)

            census = Census.objects.filter(voting_id=vid)
        
            total_unique_voters = Vote.objects.filter(voting_id=vid).values('voter_id').distinct().count()

            total_voters_in_census = census.count()

            no_votes = total_voters_in_census - total_unique_voters

            centros_distintos = Census.objects.values('adscription_center').distinct()
            centros = [censo['adscription_center'] for censo in centros_distintos]

            for centro in centros:
                votos = 0
                for censo in census:
                    if censo.adscription_center == centro:
                        votos += 1
                centros[centros.index(centro)] = {'name': centro, 'value': votos}

            context['census'] = json.dumps(centros)
            context['total_votes'] = json.dumps(total_unique_voters)
            context['no_votes'] = json.dumps(no_votes)

        except:
            raise Http404

        return context
    
def listVisualizer(request):
    if request.user.is_superuser:
        visualizers=[]
        visualizerAll=Voting.objects.all()
        for visualizer in visualizerAll:
            if visualizer.start_date is not None:
                visualizers.append(visualizer)
        return render(request,'visualizer/listVisualizer.html',{'visualizers': visualizers})
    elif request.user.is_authenticated:
        censos=Census.objects.filter(voter_id=request.user.id)
        visualizers=[]
        for censo in censos:
            visualizerMyCenso=Voting.objects.filter(id=censo.voting_id)
            for visualizer in visualizerMyCenso:
                if visualizer.end_date is not None:
                    visualizers.append(visualizer)
        return render(request,'visualizer/listVisualizer.html',{'visualizers': visualizers})
    else:
        return redirect('/users/login')
