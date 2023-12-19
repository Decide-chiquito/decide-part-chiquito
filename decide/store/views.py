from django.shortcuts import get_object_or_404
from django.utils import timezone
from django.utils.dateparse import parse_datetime
import django_filters.rest_framework
from rest_framework import status
from rest_framework.response import Response
from rest_framework import generics

from .models import Vote
from .serializers import VoteSerializer
from base import mods
from base.perms import UserIsStaff


class StoreView(generics.ListAPIView):
    queryset = Vote.objects.all()
    serializer_class = VoteSerializer
    filter_backends = (django_filters.rest_framework.DjangoFilterBackend,)
    filterset_fields = ('voting_id', 'question_id', 'voter_id')

    def get(self, request):
        self.permission_classes = (UserIsStaff,)
        self.check_permissions(request)
        return super().get(request)

    def post(self, request):
        """
         * voting: id
         * voter: id
         * token: token
         * votes: [ { "questionId": id, "vote": { "a": int, "b": int } } ]
        """

        vid = request.data.get('voting')
        uid = request.data.get('voter')
        votes_list = request.data.get('votes')

        voting = mods.get('voting', params={'id': vid})

        if not voting or not isinstance(voting, list):
            # print("por aqui 35")
            return Response({}, status=status.HTTP_401_UNAUTHORIZED)

        start_date = voting[0].get('start_date', None)
        # print ("Start date: "+  start_date)
        end_date = voting[0].get('end_date', None)
        #print ("End date: ", end_date)
        not_started = not start_date or timezone.now() < parse_datetime(start_date)
        #print (not_started)
        is_closed = end_date and parse_datetime(end_date) < timezone.now()
        if not_started or is_closed:
            #print("por aqui 42")
            return Response({}, status=status.HTTP_401_UNAUTHORIZED)

        # validating voter
        # if request.auth:
        #     token = request.auth.key
        # else:
        #     token = "NO-AUTH-VOTE"
        # voter = mods.post('authentication', entry_point='/getuser/', json={'token': token})
        # voter_id = voter.get('id', None)
        # if not voter_id or voter_id != uid:
        #     # print("por aqui 59")
        #     return Response({}, status=status.HTTP_401_UNAUTHORIZED)

        # the user is in the census
        perms = mods.get('census/{}'.format(vid), params={'voter_id': uid}, response=True)
        if perms.status_code == 401:
            # print("por aqui 65")
            return Response({}, status=status.HTTP_401_UNAUTHORIZED)
        
        if voting[0].get('single_vote'):
            existing_votes = Vote.objects.filter(voting_id=vid, voter_id=uid)
            if existing_votes.exists():
                return Response(
                    {},
                    status=status.HTTP_401_UNAUTHORIZED
                )
    
        for vote_data in votes_list:
            question_id = vote_data.get('questionId')
            vote = vote_data.get('vote')

            if not vid or not uid or not vote:
                return Response({}, status=status.HTTP_400_BAD_REQUEST)

            if not question_id or not vote:
                return Response({}, status=status.HTTP_400_BAD_REQUEST)

            a = vote.get("a")
            b = vote.get("b")

            defs = { "a": a, "b": b }
            v, created = Vote.objects.get_or_create(voting_id=vid, voter_id=uid, question_id=question_id,
                                                    defaults=defs)
            if not created:
                # Si el voto ya existe, actualiza los valores
                v.a = a
                v.b = b
                v.save()

        return Response({'success': 'Votes were successfully submitted.'}, status=status.HTTP_200_OK)
class StoreDetail(generics.RetrieveUpdateDestroyAPIView):
    permission_classes = (UserIsStaff,)

    def retrieve(self, request, vote_id, *args, **kwargs):
        vote = get_object_or_404(Vote, pk=vote_id)
        return Response(VoteSerializer(vote).data, status=status.HTTP_200_OK)

    def update(self, request, vote_id, *args, **kwargs):
        vote = get_object_or_404(Vote, pk=vote_id)
        a = request.data.get('a')
        b = request.data.get('b')
        if a:
            vote.a = a
        if b:
            vote.b = b
        vote.save()
        return Response("Vote updated", status=status.HTTP_204_NO_CONTENT)

    def delete(self, request, vote_id, *args, **kwargs):
        vote = get_object_or_404(Vote, pk=vote_id)
        vote.delete()
        return Response("Vote deleted", status=status.HTTP_204_NO_CONTENT)

