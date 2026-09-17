<?xml version='1.0' encoding='utf-8'?>
<ns0:gameSystem xmlns:ns0="http://www.battlescribe.net/schema/gameSystemSchema" id="sys-a1d2-5ede-e74f-7479" name="Prohammer 30k" revision="47" battleScribeVersion="2.03" authorName="Prohammer 30k Project" type="gameSystem">
  <ns0:comment>Horus Heresy army lists adapted for use with ProHammer Classic.</ns0:comment>
  <ns0:readme>Core system skeleton for Prohammer 30k. Contains points, core profile types, battlefield roles, mandatory Army Configuration and the standard Force Organisation Chart.</ns0:readme>
  <ns0:costTypes>
    <ns0:costType id="pts" name="Points" defaultCostLimit="-1" hidden="false" />
  </ns0:costTypes>
  <ns0:profileTypes>
    <ns0:profileType id="prof-model" name="Model">
      <ns0:characteristicTypes>
        <ns0:characteristicType id="model-ws" name="WS" />
        <ns0:characteristicType id="model-bs" name="BS" />
        <ns0:characteristicType id="model-s" name="S" />
        <ns0:characteristicType id="model-t" name="T" />
        <ns0:characteristicType id="model-w" name="W" />
        <ns0:characteristicType id="model-i" name="I" />
        <ns0:characteristicType id="model-a" name="A" />
        <ns0:characteristicType id="model-ld" name="Ld" />
        <ns0:characteristicType id="model-sv" name="Sv" />
      </ns0:characteristicTypes>
    </ns0:profileType>
    <ns0:profileType id="prof-ranged" name="Ranged Weapon">
      <ns0:characteristicTypes>
        <ns0:characteristicType id="ranged-range" name="Range" />
        <ns0:characteristicType id="ranged-s" name="S" />
        <ns0:characteristicType id="ranged-ap" name="AP" />
        <ns0:characteristicType id="ranged-type" name="Type" />
      </ns0:characteristicTypes>
    </ns0:profileType>
    <ns0:profileType id="prof-vehicle" name="Vehicle">
      <ns0:characteristicTypes>
        <ns0:characteristicType id="vehicle-bs" name="BS" />
        <ns0:characteristicType id="vehicle-front" name="Front" />
        <ns0:characteristicType id="vehicle-side" name="Side" />
        <ns0:characteristicType id="vehicle-rear" name="Rear" />
        <ns0:characteristicType id="vehicle-sp" name="SP" />
      </ns0:characteristicTypes>
    </ns0:profileType>
    <ns0:profileType id="prof-walker" name="Walker">
      <ns0:characteristicTypes>
        <ns0:characteristicType id="walker-ws" name="WS" />
        <ns0:characteristicType id="walker-bs" name="BS" />
        <ns0:characteristicType id="walker-s" name="S" />
        <ns0:characteristicType id="walker-front" name="Front" />
        <ns0:characteristicType id="walker-side" name="Side" />
        <ns0:characteristicType id="walker-rear" name="Rear" />
        <ns0:characteristicType id="walker-i" name="I" />
        <ns0:characteristicType id="walker-a" name="A" />
      </ns0:characteristicTypes>
    </ns0:profileType>
  </ns0:profileTypes>
  <ns0:categoryEntries>
    <ns0:categoryEntry id="cat-hq" name="HQ" hidden="false" />
    <ns0:categoryEntry id="cat-troops" name="Troops" hidden="false" />
    <ns0:categoryEntry id="cat-elites" name="Elites" hidden="false" />
    <ns0:categoryEntry id="cat-fast" name="Fast Attack" hidden="false" />
    <ns0:categoryEntry id="cat-heavy" name="Heavy Support" hidden="false" />
    <ns0:categoryEntry id="cat-transport" name="Dedicated Transport" hidden="false" />
    <ns0:categoryEntry id="cat-low" name="Lords of War" hidden="false" />
    <ns0:categoryEntry id="cat-config" name="Configuration" hidden="false" />
    <ns0:categoryEntry id="cat-aero" name="Aeronautica Imperialis" hidden="false" />
    <ns0:categoryEntry id="cat-retinue" name="Retinue" hidden="false" />
    <ns0:categoryEntry id="cat-dg-mobile" name="Death Guard Mobile Support Limit" hidden="true" />
    <ns0:categoryEntry id="cat-auxiliary" name="Auxiliary" hidden="false" />
    <ns0:categoryEntry id="cat-alpha-reward" name="Rewards of Treachery Limit" hidden="true" />
    <ns0:categoryEntry id="r47-cat-wb-favour" name="Word Bearers Favour of the Pantheon Limit" hidden="true" />
    <ns0:categoryEntry id="r63-sw-cat-grey-slayer" name="Space Wolves Grey Slayer Requirement" hidden="true" />
    <ns0:categoryEntry id="r64-if-cat-stone-comp" name="Stone Gauntlet Compulsory Troops" hidden="true" />
    <ns0:categoryEntry id="r64-if-cat-templar-comp" name="Templar Assault Compulsory Troops" hidden="true" />
    <ns0:categoryEntry id="r64-if-cat-templar-limit" name="Templar Brethren 0-1" hidden="true" />
    <ns0:categoryEntry id="r64-if-cat-tarantula-limit" name="Tarantula Batteries 0-2" hidden="true" />
    <ns0:categoryEntry id="r66-if-cat-stone-shield-ic" name="Stone Gauntlet — Shield-bearing Independent Character" hidden="true" />
    <ns0:categoryEntry id="r66-if-cat-hammer-warlord" name="Hammerfall — Warlord with Teleportation Transponders" hidden="true" />
    <ns0:categoryEntry id="r66-if-cat-templar-warlord" name="Templar Assault — Warlord with qualifying melee weapon" hidden="true" />
    <ns0:categoryEntry id="r71-nl-cat-terror-assault-comp" name="Terror Assault compulsory Terror formation" hidden="true" />
    <ns0:categoryEntry id="r71-nl-cat-horror-comp" name="Horror Cult compulsory Night Raptor" hidden="true" />
    <ns0:categoryEntry id="r74-ba-cat-revelation-comp" name="Day of Revelation — compulsory Assault/Veteran Troops" hidden="true" />
    <ns0:categoryEntry id="r74-ba-cat-sorrows-comp" name="Day of Sorrows — compulsory Tactical/Assault/Breacher Troops" hidden="true" />
    <ns0:categoryEntry id="r75-ba-cat-rev-warlord-jump" name="Day of Revelation — Warlord with Jump Pack" hidden="true" />
    <ns0:categoryEntry id="r79-ih-bitter-comp" name="Company of Bitter Iron — compulsory Medusan Immortal" hidden="true" />
    <ns0:categoryEntry id="r80-ih-bitter-comp" name="Company of Bitter Iron — compulsory Medusan Immortal" hidden="true" />
    <ns0:categoryEntry id="r80-ih-head-nonforge-consul" name="Head of the Gorgon — non-Forge-Lord Consuls" hidden="true" />
  </ns0:categoryEntries>
  <ns0:forceEntries>
    <ns0:forceEntry id="force-standard" name="Standard Age of Darkness Detachment" hidden="false">
      <ns0:categoryLinks>
        <ns0:categoryLink id="fl-config" name="Configuration" hidden="false" targetId="cat-config">
          <ns0:constraints>
            <ns0:constraint id="fl-config-min" field="selections" scope="parent" value="1" percentValue="false" shared="true" includeChildSelections="false" includeChildForces="false" type="min" />
            <ns0:constraint id="fl-config-max" field="selections" scope="parent" value="1" percentValue="false" shared="true" includeChildSelections="false" includeChildForces="false" type="max" />
          </ns0:constraints>
        </ns0:categoryLink>
        <ns0:categoryLink id="fl-hq" name="HQ" hidden="false" targetId="cat-hq">
          <ns0:constraints>
            <ns0:constraint id="fl-hq-min" field="selections" scope="parent" value="1" percentValue="false" shared="true" includeChildSelections="false" includeChildForces="false" type="min" />
            <ns0:constraint id="fl-hq-max" field="selections" scope="parent" value="2" percentValue="false" shared="true" includeChildSelections="false" includeChildForces="false" type="max" />
          </ns0:constraints>
          <ns0:modifiers>
            <ns0:modifier id="r45-um-hq-max" type="set" value="4" field="fl-hq-max">
              <ns0:conditions>
                <ns0:condition type="atLeast" value="1" field="selections" scope="roster" childId="legion-xiii" shared="true" includeChildSelections="true" includeChildForces="false" />
              </ns0:conditions>
            </ns0:modifier>
            <ns0:modifier id="r45-um-logos-hq-min" type="set" value="2" field="fl-hq-min">
              <ns0:conditions>
                <ns0:condition type="atLeast" value="1" field="selections" scope="roster" childId="r25-rite-xiii-0-the-logos-lectora" shared="true" includeChildSelections="true" includeChildForces="false" />
              </ns0:conditions>
            </ns0:modifier>
            <ns0:modifier id="r62-sw-hq-min-reset" type="set" value="0" field="fl-hq-min">
              <ns0:conditionGroups>
                <ns0:conditionGroup type="and">
                  <ns0:conditions>
                    <ns0:condition type="atLeast" value="1" field="selections" scope="roster" childId="legion-vi" shared="true" includeChildSelections="true" includeChildForces="false" />
                    <ns0:condition type="greaterThan" value="0" field="limit::pts" scope="roster" childId="model" shared="true" includeChildSelections="true" includeChildForces="false" />
                  </ns0:conditions>
                </ns0:conditionGroup>
              </ns0:conditionGroups>
            </ns0:modifier>
            <ns0:modifier id="r62-sw-hq-max-reset" type="set" value="0" field="fl-hq-max">
              <ns0:conditionGroups>
                <ns0:conditionGroup type="and">
                  <ns0:conditions>
                    <ns0:condition type="atLeast" value="1" field="selections" scope="roster" childId="legion-vi" shared="true" includeChildSelections="true" includeChildForces="false" />
                    <ns0:condition type="greaterThan" value="0" field="limit::pts" scope="roster" childId="model" shared="true" includeChildSelections="true" includeChildForces="false" />
                  </ns0:conditions>
                </ns0:conditionGroup>
              </ns0:conditionGroups>
            </ns0:modifier>
            <ns0:modifier id="r62-sw-hq-min-scale" type="increment" value="1" field="fl-hq-min">
              <ns0:repeats>
                <ns0:repeat field="limit::pts" scope="roster" value="750" shared="true" childId="model" includeChildSelections="true" includeChildForces="false" repeats="1" roundUp="true" />
              </ns0:repeats>
              <ns0:conditionGroups>
                <ns0:conditionGroup type="and">
                  <ns0:conditions>
                    <ns0:condition type="atLeast" value="1" field="selections" scope="roster" childId="legion-vi" shared="true" includeChildSelections="true" includeChildForces="false" />
                    <ns0:condition type="greaterThan" value="0" field="limit::pts" scope="roster" childId="model" shared="true" includeChildSelections="true" includeChildForces="false" />
                  </ns0:conditions>
                </ns0:conditionGroup>
              </ns0:conditionGroups>
            </ns0:modifier>
            <ns0:modifier id="r62-sw-hq-max-scale" type="increment" value="1" field="fl-hq-max">
              <ns0:repeats>
                <ns0:repeat field="limit::pts" scope="roster" value="750" shared="true" childId="model" includeChildSelections="true" includeChildForces="false" repeats="1" roundUp="true" />
              </ns0:repeats>
              <ns0:conditionGroups>
                <ns0:conditionGroup type="and">
                  <ns0:conditions>
                    <ns0:condition type="atLeast" value="1" field="selections" scope="roster" childId="legion-vi" shared="true" includeChildSelections="true" includeChildForces="false" />
                    <ns0:condition type="greaterThan" value="0" field="limit::pts" scope="roster" childId="model" shared="true" includeChildSelections="true" includeChildForces="false" />
                  </ns0:conditions>
                </ns0:conditionGroup>
              </ns0:conditionGroups>
            </ns0:modifier>
            <ns0:modifier id="r62-sw-hq-unlimited-max" type="set" value="4" field="fl-hq-max">
              <ns0:conditionGroups>
                <ns0:conditionGroup type="and">
                  <ns0:conditions>
                    <ns0:condition type="atLeast" value="1" field="selections" scope="roster" childId="legion-vi" shared="true" includeChildSelections="true" includeChildForces="false" />
                    <ns0:condition type="lessThan" value="0" field="limit::pts" scope="roster" childId="model" shared="true" includeChildSelections="true" includeChildForces="false" />
                  </ns0:conditions>
                </ns0:conditionGroup>
              </ns0:conditionGroups>
            </ns0:modifier>
            <ns0:modifier id="r71-nl-mawdrym-hq-min" type="set" value="2" field="fl-hq-min">
              <ns0:conditionGroups>
                <ns0:conditionGroup type="and">
                  <ns0:conditions>
                    <ns0:condition type="atLeast" value="1" field="selections" scope="roster" childId="r41-unit-viii-8-flaymaster-mawdrym-llansahai" shared="true" includeChildSelections="true" includeChildForces="false" />
                    <ns0:condition type="lessThan" value="1" field="selections" scope="roster" childId="da22-rite-primarchs-chosen" shared="true" includeChildSelections="true" includeChildForces="false" />
                  </ns0:conditions>
                </ns0:conditionGroup>
              </ns0:conditionGroups>
            </ns0:modifier>
          </ns0:modifiers>
        </ns0:categoryLink>
        <ns0:categoryLink id="fl-troops" name="Troops" hidden="false" targetId="cat-troops">
          <ns0:constraints>
            <ns0:constraint id="fl-troops-min" field="selections" scope="parent" value="2" percentValue="false" shared="true" includeChildSelections="false" includeChildForces="false" type="min" />
            <ns0:constraint id="fl-troops-max" field="selections" scope="parent" value="6" percentValue="false" shared="true" includeChildSelections="false" includeChildForces="false" type="max" />
          </ns0:constraints>
          <ns0:modifiers>
            <ns0:modifier id="r45-um-logos-troops-min" type="set" value="3" field="fl-troops-min">
              <ns0:conditions>
                <ns0:condition type="atLeast" value="1" field="selections" scope="roster" childId="r25-rite-xiii-0-the-logos-lectora" shared="true" includeChildSelections="true" includeChildForces="false" />
              </ns0:conditions>
            </ns0:modifier>
            <ns0:modifier id="r46-al-coils-troops-min" type="set" value="3" field="fl-troops-min">
              <ns0:conditions>
                <ns0:condition type="atLeast" value="1" field="selections" scope="roster" childId="r25-rite-xx-0-the-coils-of-the-hydra" shared="true" includeChildSelections="true" includeChildForces="false" />
              </ns0:conditions>
            </ns0:modifier>
          </ns0:modifiers>
        </ns0:categoryLink>
        <ns0:categoryLink id="fl-elites" name="Elites" hidden="false" targetId="cat-elites">
          <ns0:constraints>
            <ns0:constraint id="fl-elites-max" field="selections" scope="parent" value="3" percentValue="false" shared="true" includeChildSelections="false" includeChildForces="false" type="max" />
          </ns0:constraints>
        </ns0:categoryLink>
        <ns0:categoryLink id="fl-fast" name="Fast Attack" hidden="false" targetId="cat-fast">
          <ns0:constraints>
            <ns0:constraint id="fl-fast-max" field="selections" scope="parent" value="3" percentValue="false" shared="true" includeChildSelections="false" includeChildForces="false" type="max" />
          </ns0:constraints>
          <ns0:modifiers>
            <ns0:modifier id="r43-iw-fast-max" type="set" value="1" field="fl-fast-max">
              <ns0:conditions>
                <ns0:condition type="atLeast" value="1" field="selections" scope="roster" childId="legion-iv" shared="true" includeChildSelections="true" includeChildForces="false" />
              </ns0:conditions>
            </ns0:modifier>
            <ns0:modifier id="r64-if-stone-fast-max" type="set" value="1" field="fl-fast-max">
              <ns0:conditions>
                <ns0:condition type="atLeast" value="1" field="selections" scope="roster" childId="r25-rite-vii-0-the-stone-gauntlet" shared="true" includeChildSelections="true" includeChildForces="false" />
              </ns0:conditions>
            </ns0:modifier>
            <ns0:modifier id="r64-if-templar-fast-max" type="set" value="1" field="fl-fast-max">
              <ns0:conditions>
                <ns0:condition type="atLeast" value="1" field="selections" scope="roster" childId="r25-rite-vii-2-templar-assault" shared="true" includeChildSelections="true" includeChildForces="false" />
              </ns0:conditions>
            </ns0:modifier>
            <ns0:modifier id="r73-nl-fl-fast" type="set" value="4" field="fl-fast-max">
              <ns0:conditions>
                <ns0:condition type="atLeast" value="1" field="selections" scope="roster" childId="legion-viii" shared="true" includeChildSelections="true" includeChildForces="false" />
              </ns0:conditions>
            </ns0:modifier>
            <ns0:modifier id="r80-ih-head-fast-max" type="set" value="1" field="fl-fast-max">
              <ns0:conditions>
                <ns0:condition type="atLeast" value="1" field="selections" scope="roster" childId="r25-rite-x-0-the-head-of-the-gorgon" shared="true" includeChildSelections="true" includeChildForces="false" />
              </ns0:conditions>
            </ns0:modifier>
          </ns0:modifiers>
        </ns0:categoryLink>
        <ns0:categoryLink id="fl-heavy" name="Heavy Support" hidden="false" targetId="cat-heavy">
          <ns0:constraints>
            <ns0:constraint id="fl-heavy-max" field="selections" scope="parent" value="3" percentValue="false" shared="true" includeChildSelections="false" includeChildForces="false" type="max" />
          </ns0:constraints>
          <ns0:modifiers>
            <ns0:modifier id="r43-ec-maru-heavy-max" type="set" value="2" field="fl-heavy-max">
              <ns0:conditions>
                <ns0:condition type="atLeast" value="1" field="selections" scope="roster" childId="r25-rite-iii-0-the-maru-skara" shared="true" includeChildSelections="true" includeChildForces="false" />
              </ns0:conditions>
            </ns0:modifier>
            <ns0:modifier id="r43-iw-heavy-max" type="set" value="4" field="fl-heavy-max">
              <ns0:conditions>
                <ns0:condition type="atLeast" value="1" field="selections" scope="roster" childId="legion-iv" shared="true" includeChildSelections="true" includeChildForces="false" />
              </ns0:conditions>
            </ns0:modifier>
            <ns0:modifier id="r43-sw-pale-heavy-max" type="set" value="1" field="fl-heavy-max">
              <ns0:conditions>
                <ns0:condition type="atLeast" value="1" field="selections" scope="roster" childId="r25-rite-vi-0-the-pale-hunters" shared="true" includeChildSelections="true" includeChildForces="false" />
              </ns0:conditions>
            </ns0:modifier>
            <ns0:modifier id="r45-we-berserker-heavy-max" type="set" value="1" field="fl-heavy-max">
              <ns0:conditions>
                <ns0:condition type="atLeast" value="1" field="selections" scope="roster" childId="r25-rite-xii-0-berserker-assault" shared="true" includeChildSelections="true" includeChildForces="false" />
              </ns0:conditions>
            </ns0:modifier>
            <ns0:modifier id="r46-wb-dark-brethren-heavy-max" type="set" value="1" field="fl-heavy-max">
              <ns0:conditions>
                <ns0:condition type="atLeast" value="1" field="selections" scope="roster" childId="r25-rite-xvii-0-the-dark-brethren" shared="true" includeChildSelections="true" includeChildForces="false" />
              </ns0:conditions>
            </ns0:modifier>
            <ns0:modifier id="r46-rg-decap-heavy-max" type="set" value="1" field="fl-heavy-max">
              <ns0:conditions>
                <ns0:condition type="atLeast" value="1" field="selections" scope="roster" childId="r25-rite-xix-0-decapitation-strike" shared="true" includeChildSelections="true" includeChildForces="false" />
              </ns0:conditions>
            </ns0:modifier>
            <ns0:modifier id="r52-ec-maru-heavy-max" type="set" value="2" field="fl-heavy-max">
              <ns0:conditions>
                <ns0:condition type="atLeast" value="1" field="selections" scope="roster" childId="r25-rite-iii-0-the-maru-skara" shared="true" includeChildSelections="true" includeChildForces="false" />
              </ns0:conditions>
            </ns0:modifier>
            <ns0:modifier id="r73-nl-fl-heavy" type="set" value="1" field="fl-heavy-max">
              <ns0:conditions>
                <ns0:condition type="atLeast" value="1" field="selections" scope="roster" childId="legion-viii" shared="true" includeChildSelections="true" includeChildForces="false" />
              </ns0:conditions>
            </ns0:modifier>
            <ns0:modifier id="r74-ba-rev-heavy-max" type="set" value="1" field="fl-heavy-max">
              <ns0:conditions>
                <ns0:condition type="atLeast" value="1" field="selections" scope="roster" childId="r25-rite-ix-0-the-day-of-revelation" shared="true" includeChildSelections="true" includeChildForces="false" />
              </ns0:conditions>
            </ns0:modifier>
            <ns0:modifier id="r75-ba-rev-heavy-max" type="set" value="1" field="fl-heavy-max">
              <ns0:conditions>
                <ns0:condition type="atLeast" value="1" field="selections" scope="roster" childId="r25-rite-ix-0-the-day-of-revelation" shared="true" includeChildSelections="true" includeChildForces="false" />
              </ns0:conditions>
            </ns0:modifier>
          </ns0:modifiers>
        </ns0:categoryLink>
        <ns0:categoryLink id="fl-transport" name="Dedicated Transport" hidden="false" targetId="cat-transport" />
        <ns0:categoryLink id="fl-low" name="Lords of War" hidden="false" targetId="cat-low">
          <ns0:constraints>
            <ns0:constraint id="fl-low-max" field="selections" scope="parent" value="1" percentValue="false" shared="true" includeChildSelections="false" includeChildForces="false" type="max" />
          </ns0:constraints>
        </ns0:categoryLink>
        <ns0:categoryLink id="fl-retinue" name="Retinue" hidden="false" targetId="cat-retinue" />
        <ns0:categoryLink id="fl-dg-mobile" name="Death Guard Mobile Support Limit" targetId="cat-dg-mobile" hidden="true">
          <ns0:constraints>
            <ns0:constraint id="r45-dg-mobile-max" field="selections" scope="parent" value="1" type="max" shared="true" includeChildSelections="false" includeChildForces="false" />
          </ns0:constraints>
        </ns0:categoryLink>
        <ns0:categoryLink id="fl-auxiliary" name="Auxiliary" targetId="cat-auxiliary" hidden="false" />
        <ns0:categoryLink id="fl-alpha-reward" name="Rewards of Treachery Limit" targetId="cat-alpha-reward" hidden="true">
          <ns0:constraints>
            <ns0:constraint id="r46-al-reward-max" field="selections" scope="parent" value="1" type="max" shared="true" includeChildSelections="false" includeChildForces="false" />
          </ns0:constraints>
        </ns0:categoryLink>
        <ns0:categoryLink id="r47-fl-wb-favour" name="Word Bearers Favour Limit" targetId="r47-cat-wb-favour" hidden="true">
          <ns0:constraints>
            <ns0:constraint id="r47-wb-favour-roster-max" field="selections" scope="roster" value="1" type="max" shared="true" includeChildSelections="true" includeChildForces="false" />
          </ns0:constraints>
        </ns0:categoryLink>
        <ns0:categoryLink id="r63-sw-fl-grey-slayer" name="Grey Slayer Requirement" hidden="true" targetId="r63-sw-cat-grey-slayer">
          <ns0:constraints>
            <ns0:constraint id="r63-sw-grey-slayer-min" type="min" value="0" field="selections" scope="parent" shared="true" includeChildSelections="false" includeChildForces="false" />
          </ns0:constraints>
          <ns0:modifiers>
            <ns0:modifier id="r63-sw-grey-slayer-min-mod" type="set" value="1" field="r63-sw-grey-slayer-min">
              <ns0:conditions>
                <ns0:condition type="atLeast" value="1" field="selections" scope="roster" childId="r25-rite-vi-1-the-bloodied-claws" shared="true" includeChildSelections="true" includeChildForces="false" />
              </ns0:conditions>
            </ns0:modifier>
          </ns0:modifiers>
        </ns0:categoryLink>
        <ns0:categoryLink id="r64-if-fl-r64-if-cat-stone-comp" name="Stone Gauntlet Compulsory Troops" hidden="true" targetId="r64-if-cat-stone-comp">
          <ns0:constraints>
            <ns0:constraint id="r64-if-r64-if-cat-stone-comp-min" type="min" value="0" field="selections" scope="parent" shared="true" includeChildSelections="false" includeChildForces="false" />
          </ns0:constraints>
          <ns0:modifiers>
            <ns0:modifier id="r64-if-r64-if-cat-stone-comp-min-mod" type="set" value="2" field="r64-if-r64-if-cat-stone-comp-min">
              <ns0:conditions>
                <ns0:condition type="atLeast" value="1" field="selections" scope="roster" childId="r25-rite-vii-0-the-stone-gauntlet" shared="true" includeChildSelections="true" includeChildForces="false" />
              </ns0:conditions>
            </ns0:modifier>
          </ns0:modifiers>
        </ns0:categoryLink>
        <ns0:categoryLink id="r64-if-fl-r64-if-cat-templar-comp" name="Templar Assault Compulsory Troops" hidden="true" targetId="r64-if-cat-templar-comp">
          <ns0:constraints>
            <ns0:constraint id="r64-if-r64-if-cat-templar-comp-min" type="min" value="0" field="selections" scope="parent" shared="true" includeChildSelections="false" includeChildForces="false" />
          </ns0:constraints>
          <ns0:modifiers>
            <ns0:modifier id="r64-if-r64-if-cat-templar-comp-min-mod" type="set" value="2" field="r64-if-r64-if-cat-templar-comp-min">
              <ns0:conditions>
                <ns0:condition type="atLeast" value="1" field="selections" scope="roster" childId="r25-rite-vii-2-templar-assault" shared="true" includeChildSelections="true" includeChildForces="false" />
              </ns0:conditions>
            </ns0:modifier>
          </ns0:modifiers>
        </ns0:categoryLink>
        <ns0:categoryLink id="r64-if-fl-r64-if-cat-templar-limit" name="Templar Brethren 0-1" hidden="true" targetId="r64-if-cat-templar-limit">
          <ns0:constraints>
            <ns0:constraint id="r64-if-r64-if-cat-templar-limit-max" type="max" value="99" field="selections" scope="parent" shared="true" includeChildSelections="false" includeChildForces="false" />
          </ns0:constraints>
          <ns0:modifiers>
            <ns0:modifier id="r64-if-r64-if-cat-templar-limit-max-mod" type="set" value="1" field="r64-if-r64-if-cat-templar-limit-max">
              <ns0:conditionGroups>
                <ns0:conditionGroup type="and">
                  <ns0:conditions>
                    <ns0:condition type="atLeast" value="1" field="selections" scope="roster" childId="legion-vii" shared="true" includeChildSelections="true" includeChildForces="false" />
                    <ns0:condition type="lessThan" value="1" field="selections" scope="roster" childId="r25-rite-vii-2-templar-assault" shared="true" includeChildSelections="true" includeChildForces="false" />
                  </ns0:conditions>
                </ns0:conditionGroup>
              </ns0:conditionGroups>
            </ns0:modifier>
          </ns0:modifiers>
        </ns0:categoryLink>
        <ns0:categoryLink id="r64-if-fl-r64-if-cat-tarantula-limit" name="Tarantula Batteries 0-2" hidden="true" targetId="r64-if-cat-tarantula-limit">
          <ns0:constraints>
            <ns0:constraint id="r64-if-r64-if-cat-tarantula-limit-max" type="max" value="99" field="selections" scope="parent" shared="true" includeChildSelections="false" includeChildForces="false" />
          </ns0:constraints>
          <ns0:modifiers>
            <ns0:modifier id="r64-if-r64-if-cat-tarantula-limit-max-mod" type="set" value="2" field="r64-if-r64-if-cat-tarantula-limit-max">
              <ns0:conditions>
                <ns0:condition type="atLeast" value="1" field="selections" scope="roster" childId="legion-vii" shared="true" includeChildSelections="true" includeChildForces="false" />
              </ns0:conditions>
            </ns0:modifier>
          </ns0:modifiers>
        </ns0:categoryLink>
        <ns0:categoryLink id="r66-if-fl-r66-if-cat-stone-shield-ic" name="Stone Gauntlet — Shield-bearing Independent Character" hidden="true" targetId="r66-if-cat-stone-shield-ic">
          <ns0:constraints>
            <ns0:constraint id="r66-if-fl-r66-if-cat-stone-shield-ic-min" type="min" value="0" field="selections" scope="parent" shared="true" includeChildSelections="true" includeChildForces="false" />
          </ns0:constraints>
          <ns0:modifiers>
            <ns0:modifier id="r66-if-fl-r66-if-cat-stone-shield-ic-min-mod" type="set" value="1" field="r66-if-fl-r66-if-cat-stone-shield-ic-min">
              <ns0:conditions>
                <ns0:condition type="atLeast" value="1" field="selections" scope="roster" childId="r25-rite-vii-0-the-stone-gauntlet" shared="true" includeChildSelections="true" includeChildForces="false" />
              </ns0:conditions>
            </ns0:modifier>
          </ns0:modifiers>
        </ns0:categoryLink>
        <ns0:categoryLink id="r66-if-fl-r66-if-cat-hammer-warlord" name="Hammerfall — Warlord with Teleportation Transponders" hidden="true" targetId="r66-if-cat-hammer-warlord">
          <ns0:constraints>
            <ns0:constraint id="r66-if-fl-r66-if-cat-hammer-warlord-min" type="min" value="0" field="selections" scope="parent" shared="true" includeChildSelections="true" includeChildForces="false" />
            <ns0:constraint id="r66-if-fl-r66-if-cat-hammer-warlord-max" type="max" value="99" field="selections" scope="parent" shared="true" includeChildSelections="true" includeChildForces="false" />
          </ns0:constraints>
          <ns0:modifiers>
            <ns0:modifier id="r66-if-fl-r66-if-cat-hammer-warlord-min-mod" type="set" value="1" field="r66-if-fl-r66-if-cat-hammer-warlord-min">
              <ns0:conditions>
                <ns0:condition type="atLeast" value="1" field="selections" scope="roster" childId="r25-rite-vii-1-hammerfall-strike-force" shared="true" includeChildSelections="true" includeChildForces="false" />
              </ns0:conditions>
            </ns0:modifier>
            <ns0:modifier id="r66-if-fl-r66-if-cat-hammer-warlord-max-mod" type="set" value="1" field="r66-if-fl-r66-if-cat-hammer-warlord-max">
              <ns0:conditions>
                <ns0:condition type="atLeast" value="1" field="selections" scope="roster" childId="r25-rite-vii-1-hammerfall-strike-force" shared="true" includeChildSelections="true" includeChildForces="false" />
              </ns0:conditions>
            </ns0:modifier>
          </ns0:modifiers>
        </ns0:categoryLink>
        <ns0:categoryLink id="r66-if-fl-r66-if-cat-templar-warlord" name="Templar Assault — Warlord with qualifying melee weapon" hidden="true" targetId="r66-if-cat-templar-warlord">
          <ns0:constraints>
            <ns0:constraint id="r66-if-fl-r66-if-cat-templar-warlord-min" type="min" value="0" field="selections" scope="parent" shared="true" includeChildSelections="true" includeChildForces="false" />
            <ns0:constraint id="r66-if-fl-r66-if-cat-templar-warlord-max" type="max" value="99" field="selections" scope="parent" shared="true" includeChildSelections="true" includeChildForces="false" />
          </ns0:constraints>
          <ns0:modifiers>
            <ns0:modifier id="r66-if-fl-r66-if-cat-templar-warlord-min-mod" type="set" value="1" field="r66-if-fl-r66-if-cat-templar-warlord-min">
              <ns0:conditions>
                <ns0:condition type="atLeast" value="1" field="selections" scope="roster" childId="r25-rite-vii-2-templar-assault" shared="true" includeChildSelections="true" includeChildForces="false" />
              </ns0:conditions>
            </ns0:modifier>
            <ns0:modifier id="r66-if-fl-r66-if-cat-templar-warlord-max-mod" type="set" value="1" field="r66-if-fl-r66-if-cat-templar-warlord-max">
              <ns0:conditions>
                <ns0:condition type="atLeast" value="1" field="selections" scope="roster" childId="r25-rite-vii-2-templar-assault" shared="true" includeChildSelections="true" includeChildForces="false" />
              </ns0:conditions>
            </ns0:modifier>
          </ns0:modifiers>
        </ns0:categoryLink>
        <ns0:categoryLink id="r71-nl-fl-r71-nl-cat-terror-assault-comp" name="Terror Assault compulsory Terror formation" hidden="true" targetId="r71-nl-cat-terror-assault-comp">
          <ns0:constraints>
            <ns0:constraint id="r71-nl-r71-nl-cat-terror-assault-comp-min" type="min" value="0" field="selections" scope="parent" shared="true" includeChildSelections="false" includeChildForces="false" />
          </ns0:constraints>
          <ns0:modifiers>
            <ns0:modifier id="r71-nl-r71-nl-cat-terror-assault-comp-min-mod" type="set" value="1" field="r71-nl-r71-nl-cat-terror-assault-comp-min">
              <ns0:conditions>
                <ns0:condition type="atLeast" value="1" field="selections" scope="roster" childId="r25-rite-viii-0-terror-assault" shared="true" includeChildSelections="true" includeChildForces="false" />
              </ns0:conditions>
            </ns0:modifier>
          </ns0:modifiers>
        </ns0:categoryLink>
        <ns0:categoryLink id="r71-nl-fl-r71-nl-cat-horror-comp" name="Horror Cult compulsory Night Raptor" hidden="true" targetId="r71-nl-cat-horror-comp">
          <ns0:constraints>
            <ns0:constraint id="r71-nl-r71-nl-cat-horror-comp-min" type="min" value="0" field="selections" scope="parent" shared="true" includeChildSelections="false" includeChildForces="false" />
          </ns0:constraints>
          <ns0:modifiers>
            <ns0:modifier id="r71-nl-r71-nl-cat-horror-comp-min-mod" type="set" value="1" field="r71-nl-r71-nl-cat-horror-comp-min">
              <ns0:conditions>
                <ns0:condition type="atLeast" value="1" field="selections" scope="roster" childId="r25-rite-viii-1-horror-cult" shared="true" includeChildSelections="true" includeChildForces="false" />
              </ns0:conditions>
            </ns0:modifier>
          </ns0:modifiers>
        </ns0:categoryLink>
        <ns0:categoryLink id="r74-ba-fl-r74-ba-cat-revelation-comp" name="Day of Revelation — compulsory Assault/Veteran Troops" hidden="true" targetId="r74-ba-cat-revelation-comp">
          <ns0:constraints>
            <ns0:constraint id="r74-ba-r74-ba-cat-revelation-comp-min" type="min" value="0" field="selections" scope="parent" shared="true" includeChildSelections="false" includeChildForces="false" />
          </ns0:constraints>
          <ns0:modifiers>
            <ns0:modifier id="r74-ba-r74-ba-cat-revelation-comp-min-set" type="set" value="2" field="r74-ba-r74-ba-cat-revelation-comp-min">
              <ns0:conditions>
                <ns0:condition type="atLeast" value="1" field="selections" scope="roster" childId="r25-rite-ix-0-the-day-of-revelation" shared="true" includeChildSelections="true" includeChildForces="false" />
              </ns0:conditions>
            </ns0:modifier>
            <ns0:modifier id="r75-ba-r74-ba-cat-revelation-comp-set" type="set" value="2" field="r74-ba-r74-ba-cat-revelation-comp-min">
              <ns0:conditions>
                <ns0:condition type="atLeast" value="1" field="selections" scope="roster" childId="r25-rite-ix-0-the-day-of-revelation" shared="true" includeChildSelections="true" includeChildForces="false" />
              </ns0:conditions>
            </ns0:modifier>
          </ns0:modifiers>
        </ns0:categoryLink>
        <ns0:categoryLink id="r74-ba-fl-r74-ba-cat-sorrows-comp" name="Day of Sorrows — compulsory Tactical/Assault/Breacher Troops" hidden="true" targetId="r74-ba-cat-sorrows-comp">
          <ns0:constraints>
            <ns0:constraint id="r74-ba-r74-ba-cat-sorrows-comp-min" type="min" value="0" field="selections" scope="parent" shared="true" includeChildSelections="false" includeChildForces="false" />
          </ns0:constraints>
          <ns0:modifiers>
            <ns0:modifier id="r74-ba-r74-ba-cat-sorrows-comp-min-set" type="set" value="2" field="r74-ba-r74-ba-cat-sorrows-comp-min">
              <ns0:conditions>
                <ns0:condition type="atLeast" value="1" field="selections" scope="roster" childId="r25-rite-ix-1-the-day-of-sorrows" shared="true" includeChildSelections="true" includeChildForces="false" />
              </ns0:conditions>
            </ns0:modifier>
            <ns0:modifier id="r75-ba-r74-ba-cat-sorrows-comp-set" type="set" value="2" field="r74-ba-r74-ba-cat-sorrows-comp-min">
              <ns0:conditions>
                <ns0:condition type="atLeast" value="1" field="selections" scope="roster" childId="r25-rite-ix-1-the-day-of-sorrows" shared="true" includeChildSelections="true" includeChildForces="false" />
              </ns0:conditions>
            </ns0:modifier>
          </ns0:modifiers>
        </ns0:categoryLink>
        <ns0:categoryLink id="r75-ba-fl-r75-ba-cat-rev-warlord-jump" name="Day of Revelation — Warlord with Jump Pack" hidden="true" targetId="r75-ba-cat-rev-warlord-jump">
          <ns0:constraints>
            <ns0:constraint id="r75-ba-r75-ba-cat-rev-warlord-jump-min" type="min" value="0" field="selections" scope="parent" shared="true" includeChildSelections="true" includeChildForces="false" />
          </ns0:constraints>
          <ns0:modifiers>
            <ns0:modifier id="r75-ba-r75-ba-cat-rev-warlord-jump-set" type="set" value="1" field="r75-ba-r75-ba-cat-rev-warlord-jump-min">
              <ns0:conditions>
                <ns0:condition type="atLeast" value="1" field="selections" scope="roster" childId="r25-rite-ix-0-the-day-of-revelation" shared="true" includeChildSelections="true" includeChildForces="false" />
              </ns0:conditions>
            </ns0:modifier>
          </ns0:modifiers>
        </ns0:categoryLink>
        <ns0:categoryLink id="r79-ih-bitter-comp-link" name="Company of Bitter Iron — compulsory Medusan Immortal" hidden="true" targetId="r79-ih-bitter-comp">
          <ns0:constraints>
            <ns0:constraint id="r79-ih-bitter-comp-min" type="min" value="0" field="selections" scope="parent" shared="true" includeChildSelections="false" includeChildForces="false" />
          </ns0:constraints>
          <ns0:modifiers>
            <ns0:modifier id="r79-ih-bitter-comp-set" type="set" value="1" field="r79-ih-bitter-comp-min">
              <ns0:conditions>
                <ns0:condition type="atLeast" value="1" field="selections" scope="roster" childId="r25-rite-x-1-company-of-bitter-iron" shared="true" includeChildSelections="true" includeChildForces="false" />
              </ns0:conditions>
            </ns0:modifier>
          </ns0:modifiers>
        </ns0:categoryLink>
        <ns0:categoryLink id="r80-ih-bitter-comp-link" name="Company of Bitter Iron — compulsory Medusan Immortal" hidden="true" targetId="r80-ih-bitter-comp">
          <ns0:constraints>
            <ns0:constraint id="r80-ih-bitter-comp-min" type="min" value="0" field="selections" scope="parent" shared="true" includeChildSelections="true" includeChildForces="false" />
          </ns0:constraints>
          <ns0:modifiers>
            <ns0:modifier id="r80-ih-bitter-comp-set" type="set" value="1" field="r80-ih-bitter-comp-min">
              <ns0:conditions>
                <ns0:condition type="atLeast" value="1" field="selections" scope="roster" childId="r25-rite-x-1-company-of-bitter-iron" shared="true" includeChildSelections="true" includeChildForces="false" />
              </ns0:conditions>
            </ns0:modifier>
          </ns0:modifiers>
        </ns0:categoryLink>
        <ns0:categoryLink id="r80-ih-head-consul-link" name="Head of the Gorgon — non-Forge-Lord Consuls" hidden="true" targetId="r80-ih-head-nonforge-consul">
          <ns0:constraints>
            <ns0:constraint id="r80-ih-head-consul-max" type="max" value="99" field="selections" scope="parent" shared="true" includeChildSelections="true" includeChildForces="false" />
          </ns0:constraints>
          <ns0:modifiers>
            <ns0:modifier id="r80-ih-head-consul-set" type="set" value="1" field="r80-ih-head-consul-max">
              <ns0:conditions>
                <ns0:condition type="atLeast" value="1" field="selections" scope="roster" childId="r25-rite-x-0-the-head-of-the-gorgon" shared="true" includeChildSelections="true" includeChildForces="false" />
              </ns0:conditions>
            </ns0:modifier>
          </ns0:modifiers>
        </ns0:categoryLink>
      </ns0:categoryLinks>
    </ns0:forceEntry>
  </ns0:forceEntries>
</ns0:gameSystem>