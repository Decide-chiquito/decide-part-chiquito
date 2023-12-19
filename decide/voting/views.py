import django_filters.rest_framework
from django.conf import settings
from django.utils import timezone
from django.shortcuts import get_object_or_404
from rest_framework import generics, status
from rest_framework.response import Response
from django.utils.translation import gettext as _

from .models import Question, QuestionOption, Voting
from .serializers import SimpleVotingSerializer, VotingSerializer
from base.perms import UserIsStaff
from base.models import Auth


class VotingView(generics.ListCreateAPIView):
    queryset = Voting.objects.all()
    serializer_class = VotingSerializer
    filter_backends = (django_filters.rest_framework.DjangoFilterBackend,)
    filterset_fields = ('id',)

    def get(self, request, *args, **kwargs):
        kwargs.get('voting_id')
        self.queryset = Voting.objects.all()

        version = request.version
        if version not in settings.ALLOWED_VERSIONS:
            version = settings.DEFAULT_VERSION

        if version == 'v2':
            self.serializer_class = SimpleVotingSerializer
        return super().get(request, *args, **kwargs)

    def post(self, request, *args, **kwargs):
        self.permission_classes = (UserIsStaff,)
        self.check_permissions(request)
        for data in ['name', 'desc', 'question', 'question_opt']:
            if not data in request.data:
                return Response({"missing": data}, status=status.HTTP_400_BAD_REQUEST)

        question = Question(desc=request.data.get('question'))
        question.save()
        for idx, q_opt in enumerate(request.data.get('question_opt')):
            opt = QuestionOption(question=question, option=q_opt, number=idx)
            opt.save()
        voting = Voting(name=request.data.get('name'), desc=request.data.get('desc'),
                        question=question)
        voting.save()

        auth, _ = Auth.objects.get_or_create(url=settings.BASEURL,
                                             defaults={'me': True, 'name': 'test auth'})
        auth.save()
        voting.auths.add(auth)
        return Response({}, status=status.HTTP_201_CREATED)


class VotingAction(generics.UpdateAPIView):
    queryset = Voting.objects.all()
    serializer_class = VotingSerializer
    filter_backends = (django_filters.rest_framework.DjangoFilterBackend,)
    permission_classes = (UserIsStaff,)

    def put(self, request, voting_id, *args, **kwars):
        action = request.data.get('action')
        if not action:
            return Response({}, status=status.HTTP_400_BAD_REQUEST)

        voting = get_object_or_404(Voting, pk=voting_id)
        msg = ''
        st = status.HTTP_200_OK
        if action == 'start':
            if voting.start_date:
                msg = _('Voting already started')
                st = status.HTTP_400_BAD_REQUEST
            else:
                voting.start_date = timezone.now()
                voting.save()
                msg = _('Voting started')
        elif action == 'stop':
            if not voting.start_date:
                msg = _('Voting is not started')
                st = status.HTTP_400_BAD_REQUEST
            elif voting.end_date:
                msg = _('Voting already stopped')
                st = status.HTTP_400_BAD_REQUEST
            else:
                voting.end_date = timezone.now()
                voting.save()
                msg = _('Voting stopped')
        elif action == 'tally':
            if not voting.start_date:
                msg = _('Voting is not started')
                st = status.HTTP_400_BAD_REQUEST
            elif not voting.end_date:
                msg = _('Voting is not stopped')
                st = status.HTTP_400_BAD_REQUEST
            elif voting.tally:
                msg = _('Voting already tallied')
                st = status.HTTP_400_BAD_REQUEST
            else:
                voting.tally_votes(request.auth.key)
                msg = _('Voting tallied')
        else:
            msg = _('Action not found, try with start, stop or tally')
            st = status.HTTP_400_BAD_REQUEST
        return Response(msg, status=st)


class VotingStaff(generics.RetrieveUpdateDestroyAPIView):
    queryset = Voting.objects.all()
    serializer_class = VotingSerializer
    filter_backends = (django_filters.rest_framework.DjangoFilterBackend,)
    permission_classes = (UserIsStaff,)

    def update(self, request, voting_id, *args, **kwargs):
        voting = get_object_or_404(Voting, pk=voting_id)
        if 'name' in request.data:
            voting.name = request.data.get('name')
        if 'desc' in request.data:
            voting.desc = request.data.get('desc')
        if 'question' in request.data:
            question = Question(desc=request.data.get('question'))
            question.save()
            voting.question = question
        if 'question_opt' in request.data:
            voting.question_opt.clear()
            for idx, q_opt in enumerate(request.data.get('question_opt')):
                opt = QuestionOption(question=voting.question, option=q_opt, number=idx)
                opt.save()
                voting.question_opt.add(opt)

        voting.save()

        return Response("Voting updated", status=status.HTTP_200_OK)

    def destroy(self, request, voting_id, *args, **kwars):
        voting = get_object_or_404(Voting, pk=voting_id)
        voting.delete()
        return Response('Voting deleted', status=status.HTTP_204_NO_CONTENT)

    def retrieve(self, request, voting_id, *args, **kwars):
        voting = get_object_or_404(Voting, pk=voting_id)
        return Response(VotingSerializer(voting).data, status=status.HTTP_200_OK)
