from crowdsorting.app_resources import DBProxy


def delete_judge(judge_id):
    DBProxy.delete_judge(judge_id)
