import json
from django.views.generic import TemplateView
from django.conf import settings
from django.http import Http404
from django.shortcuts import render,redirect

from base import mods
from census.models import Census
from voting.models import Voting

# TODO: check permissions and census
class BoothView(TemplateView):
    template_name = 'booth/booth.html'

    def get_template_names(self):

        if self.request.user_agent.is_mobile:
            self.template_name = 'booth/booth_mobile.html'
        else:
            self.template_name = 'booth/booth.html'

        
        return [self.template_name]

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        vid = kwargs.get('voting_id', 0)

        try:
            r = mods.get('voting', params={'id': vid})
            # Casting numbers to string to manage in javascript with BigInt
            # and avoid problems with js and big number conversion
            for k, v in r[0]['pub_key'].items():
                r[0]['pub_key'][k] = str(v)

            context['voting'] = json.dumps(r[0])
            context['is_mobile'] = self.request.user_agent.is_mobile
        except:
            raise Http404

        context['KEYBITS'] = settings.KEYBITS

        return context

def listActiveBooth(request):
    if request.user.is_authenticated:
        censos=Census.objects.filter(voter_id=request.user.id)
        booths=[];
        for censo in censos:
            boothsMyCenso=Voting.objects.filter(id=censo.voting_id)
            for booth in boothsMyCenso:
                if booth.end_date== None:
                    booths.append(booth)
        return render(request,'booth/listBooth.html',{'booths': booths})
    else:
        return redirect('/users/login')
