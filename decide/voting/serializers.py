from rest_framework import serializers

from .models import Question, QuestionOption, Voting
from base.serializers import KeySerializer, AuthSerializer


class QuestionOptionSerializer(serializers.HyperlinkedModelSerializer):
    class Meta:
        model = QuestionOption
        fields = ('number', 'option')


class QuestionSerializer(serializers.HyperlinkedModelSerializer):
    options = QuestionOptionSerializer(many=True)
    class Meta:
        model = Question
        fields = ('id', 'desc', 'options')


class VotingSerializer(serializers.HyperlinkedModelSerializer):
    questions = QuestionSerializer(many=True)
    pub_key = KeySerializer()
    auths = AuthSerializer(many=True)

    class Meta:
        model = Voting
        fields = ('id', 'name', 'desc', 'questions', 'start_date', 'seats','method',
                  'end_date', 'pub_key', 'auths', 'tally', 'postproc', 'single_vote')


class SimpleVotingSerializer(serializers.HyperlinkedModelSerializer):
    questions = QuestionSerializer(many=True)

    class Meta:
        model = Voting
        fields = ('name', 'desc', 'questions', 'start_date', 'end_date', 'single_vote')