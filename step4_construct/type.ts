
// b-text-i-text
// <p><b>baliser</b>, <i>v.a.</i>, (nav.) to buoy, to erect beacons.</p>
// <p><b>ballon</b>, <i>n.m.</i>, balloon; football. <i>Envoyer un — d’essai</i>; to send out a feeler.</p>
type Base = {
  word: string;
  pronunciation?: string;
  pos: string;
  translation: string;
  usage?: { fr: string; en: string }[];
}

// b-text-b-text-i-text 
// b-text-b-text-i-text-i-text 
// <p><b>barbé</b>, <b>-e</b>, <i>adj.</i>, (her.) barbed, bearded; (bot.) barbated.</p>
// <p><b>barbelé</b>, <b>-e</b>, <i>adj.</i>, bearded, barbed. <i>Flèche —e</i>; barbed arrow.</p>
type BaseWithFeminine = Base & {
  metadata: {
    suffix: string;
  }
}         

// i-b-text-i-text                           
// i-b-text-i-text-i-text
// <p><i>se</i> <b>blouser</b>, <i>v.r.</i>, to hole one’s own ball; to blunder; to be in the wrong box.</p>
// <p><i>se</i> <b>battre</b>, <i>v.r.</i>, to fight, to combat, to scuffle. <i>Se — à qui aura quelque chose</i>; to scramble for something.</p>
type BaseWithReflexive = Base & {
  metadata: {
    reflexive: string;
  }
}

// text-b-text-i-text
// text-b-text-i-text-i-text
// <p>*<b>bourgogne</b>, <i>n.m.</i>, Burgundy wine.</p>
// <p>*<b>bille</b>, <i>n.f.</i>, billiard-ball; marble taw (to play with); a log, balk (of timber). <i>Faire une —</i>; to hole a ball.</p>
type BaseWithMarker = Base & {
  metadata: {
    marker: '*' | '†';
  }
}

// b-text-i-text-b-text-i-text
// <p><b>bavard</b>, <i>n.m.</i>, <b>-e</b>, <i>n.f.</i>, prater, babbler, chatterer.</p>
// <p><b>act-eur</b>, <i>n.m.</i>, <b>-rice</b>, <i>n.f.</i>, actor; actress; player.</p>
type BaseWith2GenderNoun = Base & {
  metadata: {
    feminineSuffix: string;    // e.g. "-e", "-rice", "-ve"
    femininePos: string;       // e.g. "n.f."
  }
}

// text-b-text-b-text-i-text
// <p>*<b>bouillonnant</b>, <b>-e</b>, <i>adj.</i>, bubbling, gurgling.</p>
type bouillonnant = {
  metadata: {
    marker: '*' | '†';
  }
} & BaseWithFeminine

// text-b-text-i-text-b-text-i-text
// <p>*<b>baigneu-r</b>, <i>n.m.</i>, <b>-se</b>, <i>n.f.</i>, bather, bath-keeper.</p>
type baigneur = {
  metadata: {
    marker: '*' | '†';
  }
} & BaseWith2GenderNoun

// text-i-b-text-i-text
// <p>*<i>se</i> <b>barbouiller</b>, <i>v.r.</i>, to besmear, to injure one’s character.</p>
type barbouiller = {
  metadata: {
    marker: '*' | '†';
  }
} & BaseWithReflexive


