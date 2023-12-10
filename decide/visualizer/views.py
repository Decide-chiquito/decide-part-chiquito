import json
from django.views.generic import TemplateView
from django.conf import settings
from django.http import Http404
from django.shortcuts import render,redirect, get_object_or_404

from base import mods
from census.models import Census
from voting.models import Voting

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

            token = self.request.session.get('auth-token', '')
            v = r[0]
            v_id = v['id']
            voting_instance = get_object_or_404(Voting, id=v_id)
            
            context['voting'] = json.dumps(v)
            context['is_mobile'] = self.request.user_agent.is_mobile

            # STATISTICS
            if voting_instance.end_date == None:
                live_tally = voting_instance.live_tally(token)
                context['live_tally'] = json.dumps(live_tally)

                census = Census.objects.filter(voting_id=v_id)
                total_votes = 0
                for opcion in live_tally:
                    total_votes += opcion['votes']
                no_votes = census.count() - total_votes
                
                context['votes'] = json.dumps([{'name': 'Voto Realizado', 'value': total_votes}, {'name': 'Voto No Realizado', 'value': no_votes}])

                centros_distintos = Census.objects.values('adscription_center').distinct()
                centros = [censo['adscription_center'] for censo in centros_distintos]

                for centro in centros:
                    votos = 0
                    for censo in census:
                        if censo.adscription_center == centro:
                            votos += 1
                    centros[centros.index(centro)] = {'name': centro, 'value': votos}

                context['census'] = json.dumps(centros)


        except:
            raise Http404

        return context

    
    
def listVisualizer(request):
    if request.user.is_authenticated:
        censos=Census.objects.filter(voter_id=request.user.id)
        visualizers=[];
        for censo in censos:
            visualizerMyCenso=Voting.objects.filter(id=censo.voting_id)
            for visualizer in visualizerMyCenso:
                if visualizer.end_date!= None:
                    visualizers.append(visualizer)
        return render(request,'visualizer/listVisualizer.html',{'visualizers': visualizers})
    else:
        return redirect('/users/login')
