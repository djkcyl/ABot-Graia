class HorseStatus:
    Normal = "正常"
    Slowness = "减速"
    SpeedUp = "加速"
    Freeze = "冻结"
    Dizziness = "眩晕"
    Death = "死亡"
    Shield = "护盾"
    Poisoning = "中毒"


props = {
    # 效果名            描述          值  持续回合
    "香蕉皮": (HorseStatus.Dizziness, 0, 1),
    "肥皂": (HorseStatus.Slowness, 0.5, 2),
    "冰弹": (HorseStatus.Freeze, 0, 3),
    "苹果": (HorseStatus.SpeedUp, 1.2, 1),
    "兴奋剂": (HorseStatus.SpeedUp, 1.5, 2),
    "强效兴奋剂": (HorseStatus.SpeedUp, 2, 3),
    "马蹄铁": (HorseStatus.Shield, 1, 3),
    "高级马蹄铁": (HorseStatus.Shield, 1, 5),
    "炸弹": (HorseStatus.Death, 0, 1),
    "毒药": (HorseStatus.Poisoning, 1, 8),
}
