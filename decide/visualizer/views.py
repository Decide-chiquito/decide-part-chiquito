import json
from django.views.generic import TemplateView
from django.conf import settings
from django.http import Http404

from base import mods


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
            voting = r[0]
            
            context['is_mobile'] = self.request.user_agent.is_mobile

            yesno = [{'number': 2, 'option': 'Yes'}, {'number': 1, 'option': 'No'}]
            voting['question']['type'] = 'MULTIPLE'
            if r[0]['question']['options'] == yesno:
                voting['question']['type'] = 'YESNO'
                voting['postproc'][0]['option'] = 'Sí' #TODO: Cuando se implemente el cambio de idioma, esto no es necesario si la app es en ingles, igual en el html de BOOTH
            context['voting'] = json.dumps(voting)
        except:
            raise Http404

        return context
