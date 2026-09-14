<?xml version='1.0' encoding='UTF-8'?>
<gameSystem xmlns="http://www.battlescribe.net/schema/gameSystemSchema" id="sys-a1d2-5ede-e74f-7479" name="Prohammer 30k" revision="21" battleScribeVersion="2.03" authorName="Prohammer 30k Project" type="gameSystem">
  <comment>Horus Heresy army lists adapted for use with ProHammer Classic.</comment>
  <readme>Core system skeleton for Prohammer 30k. Contains points, core profile types, battlefield roles, mandatory Army Configuration and the standard Force Organisation Chart.</readme>
  <costTypes>
    <costType id="pts" name="Points" defaultCostLimit="-1" hidden="false" />
  </costTypes>
  <profileTypes>
    <profileType id="prof-model" name="Model">
      <characteristicTypes>
        <characteristicType id="model-ws" name="WS" />
        <characteristicType id="model-bs" name="BS" />
        <characteristicType id="model-s" name="S" />
        <characteristicType id="model-t" name="T" />
        <characteristicType id="model-w" name="W" />
        <characteristicType id="model-i" name="I" />
        <characteristicType id="model-a" name="A" />
        <characteristicType id="model-ld" name="Ld" />
        <characteristicType id="model-sv" name="Sv" />
      </characteristicTypes>
    </profileType>
    <profileType id="prof-ranged" name="Ranged Weapon">
      <characteristicTypes>
        <characteristicType id="ranged-range" name="Range" />
        <characteristicType id="ranged-s" name="S" />
        <characteristicType id="ranged-ap" name="AP" />
        <characteristicType id="ranged-type" name="Type" />
      </characteristicTypes>
    </profileType>
    <profileType id="prof-vehicle" name="Vehicle">
      <characteristicTypes>
        <characteristicType id="vehicle-bs" name="BS" />
        <characteristicType id="vehicle-front" name="Front" />
        <characteristicType id="vehicle-side" name="Side" />
        <characteristicType id="vehicle-rear" name="Rear" />
      <characteristicType id="vehicle-sp" name="SP" /></characteristicTypes>
    </profileType>
    <profileType id="prof-walker" name="Walker">
      <characteristicTypes>
        <characteristicType id="walker-ws" name="WS" />
        <characteristicType id="walker-bs" name="BS" />
        <characteristicType id="walker-s" name="S" />
        <characteristicType id="walker-front" name="Front" />
        <characteristicType id="walker-side" name="Side" />
        <characteristicType id="walker-rear" name="Rear" />
        <characteristicType id="walker-i" name="I" />
        <characteristicType id="walker-a" name="A" />
      </characteristicTypes>
    </profileType>
  </profileTypes>
  <categoryEntries>
    <categoryEntry id="cat-hq" name="HQ" hidden="false" />
    <categoryEntry id="cat-troops" name="Troops" hidden="false" />
    <categoryEntry id="cat-elites" name="Elites" hidden="false" />
    <categoryEntry id="cat-fast" name="Fast Attack" hidden="false" />
    <categoryEntry id="cat-heavy" name="Heavy Support" hidden="false" />
    <categoryEntry id="cat-transport" name="Dedicated Transport" hidden="false" />
    <categoryEntry id="cat-low" name="Lords of War" hidden="false" />
    <categoryEntry id="cat-config" name="Configuration" hidden="false" />
    <categoryEntry id="cat-aero" name="Aeronautica Imperialis" hidden="false" />
  <categoryEntry id="cat-retinue" name="Retinue" hidden="false" /><categoryEntry id="cat-dg-mobile" name="Death Guard Mobile Support Limit" hidden="true" /><categoryEntry id="cat-auxiliary" name="Auxiliary" hidden="false" /><categoryEntry id="cat-alpha-reward" name="Rewards of Treachery Limit" hidden="true" /><categoryEntry id="r47-cat-wb-favour" name="Word Bearers Favour of the Pantheon Limit" hidden="true" /></categoryEntries>
  <forceEntries>
    <forceEntry id="force-standard" name="Standard Age of Darkness Detachment" hidden="false">
      <categoryLinks>
        <categoryLink id="fl-config" name="Configuration" hidden="false" targetId="cat-config">
          <constraints>
            <constraint id="fl-config-min" field="selections" scope="parent" value="1" percentValue="false" shared="true" includeChildSelections="false" includeChildForces="false" type="min" />
            <constraint id="fl-config-max" field="selections" scope="parent" value="1" percentValue="false" shared="true" includeChildSelections="false" includeChildForces="false" type="max" />
          </constraints>
        </categoryLink>
        <categoryLink id="fl-hq" name="HQ" hidden="false" targetId="cat-hq">
          <constraints>
            <constraint id="fl-hq-min" field="selections" scope="parent" value="1" percentValue="false" shared="true" includeChildSelections="false" includeChildForces="false" type="min" />
            <constraint id="fl-hq-max" field="selections" scope="parent" value="2" percentValue="false" shared="true" includeChildSelections="false" includeChildForces="false" type="max" />
          </constraints>
        <modifiers><modifier id="r43-sw-hq-max" type="set" value="4" field="fl-hq-max"><conditions><condition type="atLeast" value="1" field="selections" scope="roster" childId="legion-vi" shared="true" includeChildSelections="true" includeChildForces="false" /></conditions></modifier><modifier id="r45-um-hq-max" type="set" value="4" field="fl-hq-max"><conditions><condition type="atLeast" value="1" field="selections" scope="roster" childId="legion-xiii" shared="true" includeChildSelections="true" includeChildForces="false" /></conditions></modifier><modifier id="r45-um-logos-hq-min" type="set" value="2" field="fl-hq-min"><conditions><condition type="atLeast" value="1" field="selections" scope="roster" childId="r25-rite-xiii-0-the-logos-lectora" shared="true" includeChildSelections="true" includeChildForces="false" /></conditions></modifier></modifiers></categoryLink>
        <categoryLink id="fl-troops" name="Troops" hidden="false" targetId="cat-troops">
          <constraints>
            <constraint id="fl-troops-min" field="selections" scope="parent" value="2" percentValue="false" shared="true" includeChildSelections="false" includeChildForces="false" type="min" />
            <constraint id="fl-troops-max" field="selections" scope="parent" value="6" percentValue="false" shared="true" includeChildSelections="false" includeChildForces="false" type="max" />
          </constraints>
        <modifiers><modifier id="r45-um-logos-troops-min" type="set" value="3" field="fl-troops-min"><conditions><condition type="atLeast" value="1" field="selections" scope="roster" childId="r25-rite-xiii-0-the-logos-lectora" shared="true" includeChildSelections="true" includeChildForces="false" /></conditions></modifier><modifier id="r46-al-coils-troops-min" type="set" value="3" field="fl-troops-min"><conditions><condition type="atLeast" value="1" field="selections" scope="roster" childId="r25-rite-xx-0-the-coils-of-the-hydra" shared="true" includeChildSelections="true" includeChildForces="false" /></conditions></modifier></modifiers></categoryLink>
        <categoryLink id="fl-elites" name="Elites" hidden="false" targetId="cat-elites">
          <constraints>
            <constraint id="fl-elites-max" field="selections" scope="parent" value="3" percentValue="false" shared="true" includeChildSelections="false" includeChildForces="false" type="max" />
          </constraints>
        </categoryLink>
        <categoryLink id="fl-fast" name="Fast Attack" hidden="false" targetId="cat-fast">
          <constraints>
            <constraint id="fl-fast-max" field="selections" scope="parent" value="3" percentValue="false" shared="true" includeChildSelections="false" includeChildForces="false" type="max" />
          </constraints>
        <modifiers><modifier id="r43-iw-fast-max" type="set" value="1" field="fl-fast-max"><conditions><condition type="atLeast" value="1" field="selections" scope="roster" childId="legion-iv" shared="true" includeChildSelections="true" includeChildForces="false" /></conditions></modifier><modifier id="r44-if-stone-fast-max" type="set" value="1" field="fl-fast-max"><conditions><condition type="atLeast" value="1" field="selections" scope="roster" childId="r25-rite-vii-0-the-stone-gauntlet" shared="true" includeChildSelections="true" includeChildForces="false" /></conditions></modifier><modifier id="r44-if-templar-fast-max" type="set" value="1" field="fl-fast-max"><conditions><condition type="atLeast" value="1" field="selections" scope="roster" childId="r25-rite-vii-2-templar-assault" shared="true" includeChildSelections="true" includeChildForces="false" /></conditions></modifier><modifier id="r44-nl-fast-max" type="set" value="4" field="fl-fast-max"><conditions><condition type="atLeast" value="1" field="selections" scope="roster" childId="legion-viii" shared="true" includeChildSelections="true" includeChildForces="false" /></conditions></modifier><modifier id="r44-ih-gorgon-fast-max" type="set" value="1" field="fl-fast-max"><conditions><condition type="atLeast" value="1" field="selections" scope="roster" childId="r25-rite-x-0-the-head-of-the-gorgon" shared="true" includeChildSelections="true" includeChildForces="false" /></conditions></modifier></modifiers></categoryLink>
        <categoryLink id="fl-heavy" name="Heavy Support" hidden="false" targetId="cat-heavy">
          <constraints>
            <constraint id="fl-heavy-max" field="selections" scope="parent" value="3" percentValue="false" shared="true" includeChildSelections="false" includeChildForces="false" type="max" />
          </constraints>
        <modifiers><modifier id="r43-ec-maru-heavy-max" type="set" value="2" field="fl-heavy-max"><conditions><condition type="atLeast" value="1" field="selections" scope="roster" childId="r25-rite-iii-0-the-maru-skara" shared="true" includeChildSelections="true" includeChildForces="false" /></conditions></modifier><modifier id="r43-iw-heavy-max" type="set" value="4" field="fl-heavy-max"><conditions><condition type="atLeast" value="1" field="selections" scope="roster" childId="legion-iv" shared="true" includeChildSelections="true" includeChildForces="false" /></conditions></modifier><modifier id="r43-ws-chogorian-heavy-max" type="set" value="1" field="fl-heavy-max"><conditions><condition type="atLeast" value="1" field="selections" scope="roster" childId="r25-rite-v-0-chogorian-brotherhood" shared="true" includeChildSelections="true" includeChildForces="false" /></conditions></modifier><modifier id="r43-sw-pale-heavy-max" type="set" value="1" field="fl-heavy-max"><conditions><condition type="atLeast" value="1" field="selections" scope="roster" childId="r25-rite-vi-0-the-pale-hunters" shared="true" includeChildSelections="true" includeChildForces="false" /></conditions></modifier><modifier id="r44-nl-heavy-max" type="set" value="1" field="fl-heavy-max"><conditions><condition type="atLeast" value="1" field="selections" scope="roster" childId="legion-viii" shared="true" includeChildSelections="true" includeChildForces="false" /></conditions></modifier><modifier id="r44-ba-revelation-heavy-max" type="set" value="1" field="fl-heavy-max"><conditions><condition type="atLeast" value="1" field="selections" scope="roster" childId="r25-rite-ix-0-the-day-of-revelation" shared="true" includeChildSelections="true" includeChildForces="false" /></conditions></modifier><modifier id="r45-we-berserker-heavy-max" type="set" value="1" field="fl-heavy-max"><conditions><condition type="atLeast" value="1" field="selections" scope="roster" childId="r25-rite-xii-0-berserker-assault" shared="true" includeChildSelections="true" includeChildForces="false" /></conditions></modifier><modifier id="r46-wb-dark-brethren-heavy-max" type="set" value="1" field="fl-heavy-max"><conditions><condition type="atLeast" value="1" field="selections" scope="roster" childId="r25-rite-xvii-0-the-dark-brethren" shared="true" includeChildSelections="true" includeChildForces="false" /></conditions></modifier><modifier id="r46-rg-decap-heavy-max" type="set" value="1" field="fl-heavy-max"><conditions><condition type="atLeast" value="1" field="selections" scope="roster" childId="r25-rite-xix-0-decapitation-strike" shared="true" includeChildSelections="true" includeChildForces="false" /></conditions></modifier></modifiers></categoryLink>
        <categoryLink id="fl-transport" name="Dedicated Transport" hidden="false" targetId="cat-transport" />
        <categoryLink id="fl-low" name="Lords of War" hidden="false" targetId="cat-low"><constraints><constraint id="fl-low-max" field="selections" scope="parent" value="1" percentValue="false" shared="true" includeChildSelections="false" includeChildForces="false" type="max" /></constraints></categoryLink>
        <categoryLink id="fl-retinue" name="Retinue" hidden="false" targetId="cat-retinue" /><categoryLink id="fl-dg-mobile" name="Death Guard Mobile Support Limit" targetId="cat-dg-mobile" hidden="true"><constraints><constraint id="r45-dg-mobile-max" field="selections" scope="parent" value="1" type="max" shared="true" includeChildSelections="false" includeChildForces="false" /></constraints></categoryLink><categoryLink id="fl-auxiliary" name="Auxiliary" targetId="cat-auxiliary" hidden="false" /><categoryLink id="fl-alpha-reward" name="Rewards of Treachery Limit" targetId="cat-alpha-reward" hidden="true"><constraints><constraint id="r46-al-reward-max" field="selections" scope="parent" value="1" type="max" shared="true" includeChildSelections="false" includeChildForces="false" /></constraints></categoryLink><categoryLink id="r47-fl-wb-favour" name="Word Bearers Favour Limit" targetId="r47-cat-wb-favour" hidden="true"><constraints><constraint id="r47-wb-favour-roster-max" field="selections" scope="roster" value="1" type="max" shared="true" includeChildSelections="true" includeChildForces="false" /></constraints></categoryLink></categoryLinks>
    </forceEntry>
  </forceEntries>
</gameSystem>