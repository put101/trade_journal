from typing import List
from src.journal import TF, PA, Confidence, MultiTimeframeAnalysis, RiskManagement, Outcome, TradePosition, InitialReward, PotentialReward, EntryTime, Sessions, RR

def get_all_ignored_tags() -> List[str]:
    ignored_tags = []
    classes = [TF, PA, Confidence, MultiTimeframeAnalysis, RiskManagement, Outcome, TradePosition, InitialReward, PotentialReward, EntryTime, Sessions, RR]
    for cls in classes:
        ignored_tags.extend(cls.IGNORED_TAGS)
    return ignored_tags

def get_all_categorical_tags() -> List[str]:
    categorical_tags = []
    classes = [Confidence, MultiTimeframeAnalysis, RiskManagement, Outcome]
    for cls in classes:
        categorical_tags.extend(cls.CATEGORICAL_TAGS)
    return categorical_tags
