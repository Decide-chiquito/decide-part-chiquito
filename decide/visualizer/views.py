import json
from django.views.generic import TemplateView
from django.conf import settings
from django.http import Http404
from django.shortcuts import render,redirect

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
            context['voting'] = json.dumps(r[0])
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
