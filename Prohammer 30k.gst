<?xml version='1.0' encoding='utf-8'?>
<gameSystem xmlns="http://www.battlescribe.net/schema/gameSystemSchema" id="sys-a1d2-5ede-e74f-7479" name="Prohammer 30k" revision="44" battleScribeVersion="2.03" authorName="Prohammer 30k Project" type="gameSystem">
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
        <characteristicType id="vehicle-sp" name="SP" />
      </characteristicTypes>
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
    <categoryEntry id="cat-retinue" name="Retinue" hidden="false" />
    <categoryEntry id="cat-dg-mobile" name="Death Guard Mobile Support Limit" hidden="true" />
    <categoryEntry id="cat-auxiliary" name="Auxiliary" hidden="false" />
    <categoryEntry id="cat-alpha-reward" name="Rewards of Treachery Limit" hidden="true" />
    <categoryEntry id="r47-cat-wb-favour" name="Word Bearers Favour of the Pantheon Limit" hidden="true" />
    <categoryEntry id="r63-sw-cat-grey-slayer" name="Space Wolves Grey Slayer Requirement" hidden="true" />
    <categoryEntry id="r64-if-cat-stone-comp" name="Stone Gauntlet Compulsory Troops" hidden="true" />
    <categoryEntry id="r64-if-cat-templar-comp" name="Templar Assault Compulsory Troops" hidden="true" />
    <categoryEntry id="r64-if-cat-templar-limit" name="Templar Brethren 0-1" hidden="true" />
    <categoryEntry id="r64-if-cat-tarantula-limit" name="Tarantula Batteries 0-2" hidden="true" />
    <categoryEntry id="r66-if-cat-stone-shield-ic" name="Stone Gauntlet — Shield-bearing Independent Character" hidden="true" />
    <categoryEntry id="r66-if-cat-hammer-warlord" name="Hammerfall — Warlord with Teleportation Transponders" hidden="true" />
    <categoryEntry id="r66-if-cat-templar-warlord" name="Templar Assault — Warlord with qualifying melee weapon" hidden="true" />
    <categoryEntry id="r71-nl-cat-terror-assault-comp" name="Terror Assault compulsory Terror formation" hidden="true" />
    <categoryEntry id="r71-nl-cat-horror-comp" name="Horror Cult compulsory Night Raptor" hidden="true" />
    <categoryEntry id="r74-ba-cat-revelation-comp" name="Day of Revelation — compulsory Assault/Veteran Troops" hidden="true" />
    <categoryEntry id="r74-ba-cat-sorrows-comp" name="Day of Sorrows — compulsory Tactical/Assault/Breacher Troops" hidden="true" />
    <categoryEntry id="r75-ba-cat-rev-warlord-jump" name="Day of Revelation — Warlord with Jump Pack" hidden="true" />
  </categoryEntries>
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
          <modifiers>
            <modifier id="r45-um-hq-max" type="set" value="4" field="fl-hq-max">
              <conditions>
                <condition type="atLeast" value="1" field="selections" scope="roster" childId="legion-xiii" shared="true" includeChildSelections="true" includeChildForces="false" />
              </conditions>
            </modifier>
            <modifier id="r45-um-logos-hq-min" type="set" value="2" field="fl-hq-min">
              <conditions>
                <condition type="atLeast" value="1" field="selections" scope="roster" childId="r25-rite-xiii-0-the-logos-lectora" shared="true" includeChildSelections="true" includeChildForces="false" />
              </conditions>
            </modifier>
            <modifier id="r62-sw-hq-min-reset" type="set" value="0" field="fl-hq-min">
              <conditionGroups>
                <conditionGroup type="and">
                  <conditions>
                    <condition type="atLeast" value="1" field="selections" scope="roster" childId="legion-vi" shared="true" includeChildSelections="true" includeChildForces="false" />
                    <condition type="greaterThan" value="0" field="limit::pts" scope="roster" childId="model" shared="true" includeChildSelections="true" includeChildForces="false" />
                  </conditions>
                </conditionGroup>
              </conditionGroups>
            </modifier>
            <modifier id="r62-sw-hq-max-reset" type="set" value="0" field="fl-hq-max">
              <conditionGroups>
                <conditionGroup type="and">
                  <conditions>
                    <condition type="atLeast" value="1" field="selections" scope="roster" childId="legion-vi" shared="true" includeChildSelections="true" includeChildForces="false" />
                    <condition type="greaterThan" value="0" field="limit::pts" scope="roster" childId="model" shared="true" includeChildSelections="true" includeChildForces="false" />
                  </conditions>
                </conditionGroup>
              </conditionGroups>
            </modifier>
            <modifier id="r62-sw-hq-min-scale" type="increment" value="1" field="fl-hq-min">
              <repeats>
                <repeat field="limit::pts" scope="roster" value="750" shared="true" childId="model" includeChildSelections="true" includeChildForces="false" repeats="1" roundUp="true" />
              </repeats>
              <conditionGroups>
                <conditionGroup type="and">
                  <conditions>
                    <condition type="atLeast" value="1" field="selections" scope="roster" childId="legion-vi" shared="true" includeChildSelections="true" includeChildForces="false" />
                    <condition type="greaterThan" value="0" field="limit::pts" scope="roster" childId="model" shared="true" includeChildSelections="true" includeChildForces="false" />
                  </conditions>
                </conditionGroup>
              </conditionGroups>
            </modifier>
            <modifier id="r62-sw-hq-max-scale" type="increment" value="1" field="fl-hq-max">
              <repeats>
                <repeat field="limit::pts" scope="roster" value="750" shared="true" childId="model" includeChildSelections="true" includeChildForces="false" repeats="1" roundUp="true" />
              </repeats>
              <conditionGroups>
                <conditionGroup type="and">
                  <conditions>
                    <condition type="atLeast" value="1" field="selections" scope="roster" childId="legion-vi" shared="true" includeChildSelections="true" includeChildForces="false" />
                    <condition type="greaterThan" value="0" field="limit::pts" scope="roster" childId="model" shared="true" includeChildSelections="true" includeChildForces="false" />
                  </conditions>
                </conditionGroup>
              </conditionGroups>
            </modifier>
            <modifier id="r62-sw-hq-unlimited-max" type="set" value="4" field="fl-hq-max">
              <conditionGroups>
                <conditionGroup type="and">
                  <conditions>
                    <condition type="atLeast" value="1" field="selections" scope="roster" childId="legion-vi" shared="true" includeChildSelections="true" includeChildForces="false" />
                    <condition type="lessThan" value="0" field="limit::pts" scope="roster" childId="model" shared="true" includeChildSelections="true" includeChildForces="false" />
                  </conditions>
                </conditionGroup>
              </conditionGroups>
            </modifier>
            <modifier id="r71-nl-mawdrym-hq-min" type="set" value="2" field="fl-hq-min">
              <conditionGroups>
                <conditionGroup type="and">
                  <conditions>
                    <condition type="atLeast" value="1" field="selections" scope="roster" childId="r41-unit-viii-8-flaymaster-mawdrym-llansahai" shared="true" includeChildSelections="true" includeChildForces="false" />
                    <condition type="lessThan" value="1" field="selections" scope="roster" childId="da22-rite-primarchs-chosen" shared="true" includeChildSelections="true" includeChildForces="false" />
                  </conditions>
                </conditionGroup>
              </conditionGroups>
            </modifier>
          </modifiers>
        </categoryLink>
        <categoryLink id="fl-troops" name="Troops" hidden="false" targetId="cat-troops">
          <constraints>
            <constraint id="fl-troops-min" field="selections" scope="parent" value="2" percentValue="false" shared="true" includeChildSelections="false" includeChildForces="false" type="min" />
            <constraint id="fl-troops-max" field="selections" scope="parent" value="6" percentValue="false" shared="true" includeChildSelections="false" includeChildForces="false" type="max" />
          </constraints>
          <modifiers>
            <modifier id="r45-um-logos-troops-min" type="set" value="3" field="fl-troops-min">
              <conditions>
                <condition type="atLeast" value="1" field="selections" scope="roster" childId="r25-rite-xiii-0-the-logos-lectora" shared="true" includeChildSelections="true" includeChildForces="false" />
              </conditions>
            </modifier>
            <modifier id="r46-al-coils-troops-min" type="set" value="3" field="fl-troops-min">
              <conditions>
                <condition type="atLeast" value="1" field="selections" scope="roster" childId="r25-rite-xx-0-the-coils-of-the-hydra" shared="true" includeChildSelections="true" includeChildForces="false" />
              </conditions>
            </modifier>
          </modifiers>
        </categoryLink>
        <categoryLink id="fl-elites" name="Elites" hidden="false" targetId="cat-elites">
          <constraints>
            <constraint id="fl-elites-max" field="selections" scope="parent" value="3" percentValue="false" shared="true" includeChildSelections="false" includeChildForces="false" type="max" />
          </constraints>
        </categoryLink>
        <categoryLink id="fl-fast" name="Fast Attack" hidden="false" targetId="cat-fast">
          <constraints>
            <constraint id="fl-fast-max" field="selections" scope="parent" value="3" percentValue="false" shared="true" includeChildSelections="false" includeChildForces="false" type="max" />
          </constraints>
          <modifiers>
            <modifier id="r43-iw-fast-max" type="set" value="1" field="fl-fast-max">
              <conditions>
                <condition type="atLeast" value="1" field="selections" scope="roster" childId="legion-iv" shared="true" includeChildSelections="true" includeChildForces="false" />
              </conditions>
            </modifier>
            <modifier id="r44-ih-gorgon-fast-max" type="set" value="1" field="fl-fast-max">
              <conditions>
                <condition type="atLeast" value="1" field="selections" scope="roster" childId="r25-rite-x-0-the-head-of-the-gorgon" shared="true" includeChildSelections="true" includeChildForces="false" />
              </conditions>
            </modifier>
            <modifier id="r64-if-stone-fast-max" type="set" value="1" field="fl-fast-max">
              <conditions>
                <condition type="atLeast" value="1" field="selections" scope="roster" childId="r25-rite-vii-0-the-stone-gauntlet" shared="true" includeChildSelections="true" includeChildForces="false" />
              </conditions>
            </modifier>
            <modifier id="r64-if-templar-fast-max" type="set" value="1" field="fl-fast-max">
              <conditions>
                <condition type="atLeast" value="1" field="selections" scope="roster" childId="r25-rite-vii-2-templar-assault" shared="true" includeChildSelections="true" includeChildForces="false" />
              </conditions>
            </modifier>
            <modifier id="r73-nl-fl-fast" type="set" value="4" field="fl-fast-max">
              <conditions>
                <condition type="atLeast" value="1" field="selections" scope="roster" childId="legion-viii" shared="true" includeChildSelections="true" includeChildForces="false" />
              </conditions>
            </modifier>
          </modifiers>
        </categoryLink>
        <categoryLink id="fl-heavy" name="Heavy Support" hidden="false" targetId="cat-heavy">
          <constraints>
            <constraint id="fl-heavy-max" field="selections" scope="parent" value="3" percentValue="false" shared="true" includeChildSelections="false" includeChildForces="false" type="max" />
          </constraints>
          <modifiers>
            <modifier id="r43-ec-maru-heavy-max" type="set" value="2" field="fl-heavy-max">
              <conditions>
                <condition type="atLeast" value="1" field="selections" scope="roster" childId="r25-rite-iii-0-the-maru-skara" shared="true" includeChildSelections="true" includeChildForces="false" />
              </conditions>
            </modifier>
            <modifier id="r43-iw-heavy-max" type="set" value="4" field="fl-heavy-max">
              <conditions>
                <condition type="atLeast" value="1" field="selections" scope="roster" childId="legion-iv" shared="true" includeChildSelections="true" includeChildForces="false" />
              </conditions>
            </modifier>
            <modifier id="r43-sw-pale-heavy-max" type="set" value="1" field="fl-heavy-max">
              <conditions>
                <condition type="atLeast" value="1" field="selections" scope="roster" childId="r25-rite-vi-0-the-pale-hunters" shared="true" includeChildSelections="true" includeChildForces="false" />
              </conditions>
            </modifier>
            <modifier id="r45-we-berserker-heavy-max" type="set" value="1" field="fl-heavy-max">
              <conditions>
                <condition type="atLeast" value="1" field="selections" scope="roster" childId="r25-rite-xii-0-berserker-assault" shared="true" includeChildSelections="true" includeChildForces="false" />
              </conditions>
            </modifier>
            <modifier id="r46-wb-dark-brethren-heavy-max" type="set" value="1" field="fl-heavy-max">
              <conditions>
                <condition type="atLeast" value="1" field="selections" scope="roster" childId="r25-rite-xvii-0-the-dark-brethren" shared="true" includeChildSelections="true" includeChildForces="false" />
              </conditions>
            </modifier>
            <modifier id="r46-rg-decap-heavy-max" type="set" value="1" field="fl-heavy-max">
              <conditions>
                <condition type="atLeast" value="1" field="selections" scope="roster" childId="r25-rite-xix-0-decapitation-strike" shared="true" includeChildSelections="true" includeChildForces="false" />
              </conditions>
            </modifier>
            <modifier id="r52-ec-maru-heavy-max" type="set" value="2" field="fl-heavy-max">
              <conditions>
                <condition type="atLeast" value="1" field="selections" scope="roster" childId="r25-rite-iii-0-the-maru-skara" shared="true" includeChildSelections="true" includeChildForces="false" />
              </conditions>
            </modifier>
            <modifier id="r73-nl-fl-heavy" type="set" value="1" field="fl-heavy-max">
              <conditions>
                <condition type="atLeast" value="1" field="selections" scope="roster" childId="legion-viii" shared="true" includeChildSelections="true" includeChildForces="false" />
              </conditions>
            </modifier>
            <modifier id="r74-ba-rev-heavy-max" type="set" value="1" field="fl-heavy-max">
              <conditions>
                <condition type="atLeast" value="1" field="selections" scope="roster" childId="r25-rite-ix-0-the-day-of-revelation" shared="true" includeChildSelections="true" includeChildForces="false" />
              </conditions>
            </modifier>
            <modifier id="r75-ba-rev-heavy-max" type="set" value="1" field="fl-heavy-max">
              <conditions>
                <condition type="atLeast" value="1" field="selections" scope="roster" childId="r25-rite-ix-0-the-day-of-revelation" shared="true" includeChildSelections="true" includeChildForces="false" />
              </conditions>
            </modifier>
          </modifiers>
        </categoryLink>
        <categoryLink id="fl-transport" name="Dedicated Transport" hidden="false" targetId="cat-transport" />
        <categoryLink id="fl-low" name="Lords of War" hidden="false" targetId="cat-low">
          <constraints>
            <constraint id="fl-low-max" field="selections" scope="parent" value="1" percentValue="false" shared="true" includeChildSelections="false" includeChildForces="false" type="max" />
          </constraints>
        </categoryLink>
        <categoryLink id="fl-retinue" name="Retinue" hidden="false" targetId="cat-retinue" />
        <categoryLink id="fl-dg-mobile" name="Death Guard Mobile Support Limit" targetId="cat-dg-mobile" hidden="true">
          <constraints>
            <constraint id="r45-dg-mobile-max" field="selections" scope="parent" value="1" type="max" shared="true" includeChildSelections="false" includeChildForces="false" />
          </constraints>
        </categoryLink>
        <categoryLink id="fl-auxiliary" name="Auxiliary" targetId="cat-auxiliary" hidden="false" />
        <categoryLink id="fl-alpha-reward" name="Rewards of Treachery Limit" targetId="cat-alpha-reward" hidden="true">
          <constraints>
            <constraint id="r46-al-reward-max" field="selections" scope="parent" value="1" type="max" shared="true" includeChildSelections="false" includeChildForces="false" />
          </constraints>
        </categoryLink>
        <categoryLink id="r47-fl-wb-favour" name="Word Bearers Favour Limit" targetId="r47-cat-wb-favour" hidden="true">
          <constraints>
            <constraint id="r47-wb-favour-roster-max" field="selections" scope="roster" value="1" type="max" shared="true" includeChildSelections="true" includeChildForces="false" />
          </constraints>
        </categoryLink>
        <categoryLink id="r63-sw-fl-grey-slayer" name="Grey Slayer Requirement" hidden="true" targetId="r63-sw-cat-grey-slayer">
          <constraints>
            <constraint id="r63-sw-grey-slayer-min" type="min" value="0" field="selections" scope="parent" shared="true" includeChildSelections="false" includeChildForces="false" />
          </constraints>
          <modifiers>
            <modifier id="r63-sw-grey-slayer-min-mod" type="set" value="1" field="r63-sw-grey-slayer-min">
              <conditions>
                <condition type="atLeast" value="1" field="selections" scope="roster" childId="r25-rite-vi-1-the-bloodied-claws" shared="true" includeChildSelections="true" includeChildForces="false" />
              </conditions>
            </modifier>
          </modifiers>
        </categoryLink>
        <categoryLink id="r64-if-fl-r64-if-cat-stone-comp" name="Stone Gauntlet Compulsory Troops" hidden="true" targetId="r64-if-cat-stone-comp">
          <constraints>
            <constraint id="r64-if-r64-if-cat-stone-comp-min" type="min" value="0" field="selections" scope="parent" shared="true" includeChildSelections="false" includeChildForces="false" />
          </constraints>
          <modifiers>
            <modifier id="r64-if-r64-if-cat-stone-comp-min-mod" type="set" value="2" field="r64-if-r64-if-cat-stone-comp-min">
              <conditions>
                <condition type="atLeast" value="1" field="selections" scope="roster" childId="r25-rite-vii-0-the-stone-gauntlet" shared="true" includeChildSelections="true" includeChildForces="false" />
              </conditions>
            </modifier>
          </modifiers>
        </categoryLink>
        <categoryLink id="r64-if-fl-r64-if-cat-templar-comp" name="Templar Assault Compulsory Troops" hidden="true" targetId="r64-if-cat-templar-comp">
          <constraints>
            <constraint id="r64-if-r64-if-cat-templar-comp-min" type="min" value="0" field="selections" scope="parent" shared="true" includeChildSelections="false" includeChildForces="false" />
          </constraints>
          <modifiers>
            <modifier id="r64-if-r64-if-cat-templar-comp-min-mod" type="set" value="2" field="r64-if-r64-if-cat-templar-comp-min">
              <conditions>
                <condition type="atLeast" value="1" field="selections" scope="roster" childId="r25-rite-vii-2-templar-assault" shared="true" includeChildSelections="true" includeChildForces="false" />
              </conditions>
            </modifier>
          </modifiers>
        </categoryLink>
        <categoryLink id="r64-if-fl-r64-if-cat-templar-limit" name="Templar Brethren 0-1" hidden="true" targetId="r64-if-cat-templar-limit">
          <constraints>
            <constraint id="r64-if-r64-if-cat-templar-limit-max" type="max" value="99" field="selections" scope="parent" shared="true" includeChildSelections="false" includeChildForces="false" />
          </constraints>
          <modifiers>
            <modifier id="r64-if-r64-if-cat-templar-limit-max-mod" type="set" value="1" field="r64-if-r64-if-cat-templar-limit-max">
              <conditionGroups>
                <conditionGroup type="and">
                  <conditions>
                    <condition type="atLeast" value="1" field="selections" scope="roster" childId="legion-vii" shared="true" includeChildSelections="true" includeChildForces="false" />
                    <condition type="lessThan" value="1" field="selections" scope="roster" childId="r25-rite-vii-2-templar-assault" shared="true" includeChildSelections="true" includeChildForces="false" />
                  </conditions>
                </conditionGroup>
              </conditionGroups>
            </modifier>
          </modifiers>
        </categoryLink>
        <categoryLink id="r64-if-fl-r64-if-cat-tarantula-limit" name="Tarantula Batteries 0-2" hidden="true" targetId="r64-if-cat-tarantula-limit">
          <constraints>
            <constraint id="r64-if-r64-if-cat-tarantula-limit-max" type="max" value="99" field="selections" scope="parent" shared="true" includeChildSelections="false" includeChildForces="false" />
          </constraints>
          <modifiers>
            <modifier id="r64-if-r64-if-cat-tarantula-limit-max-mod" type="set" value="2" field="r64-if-r64-if-cat-tarantula-limit-max">
              <conditions>
                <condition type="atLeast" value="1" field="selections" scope="roster" childId="legion-vii" shared="true" includeChildSelections="true" includeChildForces="false" />
              </conditions>
            </modifier>
          </modifiers>
        </categoryLink>
        <categoryLink id="r66-if-fl-r66-if-cat-stone-shield-ic" name="Stone Gauntlet — Shield-bearing Independent Character" hidden="true" targetId="r66-if-cat-stone-shield-ic">
          <constraints>
            <constraint id="r66-if-fl-r66-if-cat-stone-shield-ic-min" type="min" value="0" field="selections" scope="parent" shared="true" includeChildSelections="true" includeChildForces="false" />
          </constraints>
          <modifiers>
            <modifier id="r66-if-fl-r66-if-cat-stone-shield-ic-min-mod" type="set" value="1" field="r66-if-fl-r66-if-cat-stone-shield-ic-min">
              <conditions>
                <condition type="atLeast" value="1" field="selections" scope="roster" childId="r25-rite-vii-0-the-stone-gauntlet" shared="true" includeChildSelections="true" includeChildForces="false" />
              </conditions>
            </modifier>
          </modifiers>
        </categoryLink>
        <categoryLink id="r66-if-fl-r66-if-cat-hammer-warlord" name="Hammerfall — Warlord with Teleportation Transponders" hidden="true" targetId="r66-if-cat-hammer-warlord">
          <constraints>
            <constraint id="r66-if-fl-r66-if-cat-hammer-warlord-min" type="min" value="0" field="selections" scope="parent" shared="true" includeChildSelections="true" includeChildForces="false" />
            <constraint id="r66-if-fl-r66-if-cat-hammer-warlord-max" type="max" value="99" field="selections" scope="parent" shared="true" includeChildSelections="true" includeChildForces="false" />
          </constraints>
          <modifiers>
            <modifier id="r66-if-fl-r66-if-cat-hammer-warlord-min-mod" type="set" value="1" field="r66-if-fl-r66-if-cat-hammer-warlord-min">
              <conditions>
                <condition type="atLeast" value="1" field="selections" scope="roster" childId="r25-rite-vii-1-hammerfall-strike-force" shared="true" includeChildSelections="true" includeChildForces="false" />
              </conditions>
            </modifier>
            <modifier id="r66-if-fl-r66-if-cat-hammer-warlord-max-mod" type="set" value="1" field="r66-if-fl-r66-if-cat-hammer-warlord-max">
              <conditions>
                <condition type="atLeast" value="1" field="selections" scope="roster" childId="r25-rite-vii-1-hammerfall-strike-force" shared="true" includeChildSelections="true" includeChildForces="false" />
              </conditions>
            </modifier>
          </modifiers>
        </categoryLink>
        <categoryLink id="r66-if-fl-r66-if-cat-templar-warlord" name="Templar Assault — Warlord with qualifying melee weapon" hidden="true" targetId="r66-if-cat-templar-warlord">
          <constraints>
            <constraint id="r66-if-fl-r66-if-cat-templar-warlord-min" type="min" value="0" field="selections" scope="parent" shared="true" includeChildSelections="true" includeChildForces="false" />
            <constraint id="r66-if-fl-r66-if-cat-templar-warlord-max" type="max" value="99" field="selections" scope="parent" shared="true" includeChildSelections="true" includeChildForces="false" />
          </constraints>
          <modifiers>
            <modifier id="r66-if-fl-r66-if-cat-templar-warlord-min-mod" type="set" value="1" field="r66-if-fl-r66-if-cat-templar-warlord-min">
              <conditions>
                <condition type="atLeast" value="1" field="selections" scope="roster" childId="r25-rite-vii-2-templar-assault" shared="true" includeChildSelections="true" includeChildForces="false" />
              </conditions>
            </modifier>
            <modifier id="r66-if-fl-r66-if-cat-templar-warlord-max-mod" type="set" value="1" field="r66-if-fl-r66-if-cat-templar-warlord-max">
              <conditions>
                <condition type="atLeast" value="1" field="selections" scope="roster" childId="r25-rite-vii-2-templar-assault" shared="true" includeChildSelections="true" includeChildForces="false" />
              </conditions>
            </modifier>
          </modifiers>
        </categoryLink>
        <categoryLink id="r71-nl-fl-r71-nl-cat-terror-assault-comp" name="Terror Assault compulsory Terror formation" hidden="true" targetId="r71-nl-cat-terror-assault-comp">
          <constraints>
            <constraint id="r71-nl-r71-nl-cat-terror-assault-comp-min" type="min" value="0" field="selections" scope="parent" shared="true" includeChildSelections="false" includeChildForces="false" />
          </constraints>
          <modifiers>
            <modifier id="r71-nl-r71-nl-cat-terror-assault-comp-min-mod" type="set" value="1" field="r71-nl-r71-nl-cat-terror-assault-comp-min">
              <conditions>
                <condition type="atLeast" value="1" field="selections" scope="roster" childId="r25-rite-viii-0-terror-assault" shared="true" includeChildSelections="true" includeChildForces="false" />
              </conditions>
            </modifier>
          </modifiers>
        </categoryLink>
        <categoryLink id="r71-nl-fl-r71-nl-cat-horror-comp" name="Horror Cult compulsory Night Raptor" hidden="true" targetId="r71-nl-cat-horror-comp">
          <constraints>
            <constraint id="r71-nl-r71-nl-cat-horror-comp-min" type="min" value="0" field="selections" scope="parent" shared="true" includeChildSelections="false" includeChildForces="false" />
          </constraints>
          <modifiers>
            <modifier id="r71-nl-r71-nl-cat-horror-comp-min-mod" type="set" value="1" field="r71-nl-r71-nl-cat-horror-comp-min">
              <conditions>
                <condition type="atLeast" value="1" field="selections" scope="roster" childId="r25-rite-viii-1-horror-cult" shared="true" includeChildSelections="true" includeChildForces="false" />
              </conditions>
            </modifier>
          </modifiers>
        </categoryLink>
        <categoryLink id="r74-ba-fl-r74-ba-cat-revelation-comp" name="Day of Revelation — compulsory Assault/Veteran Troops" hidden="true" targetId="r74-ba-cat-revelation-comp">
          <constraints>
            <constraint id="r74-ba-r74-ba-cat-revelation-comp-min" type="min" value="0" field="selections" scope="parent" shared="true" includeChildSelections="false" includeChildForces="false" />
          </constraints>
          <modifiers>
            <modifier id="r74-ba-r74-ba-cat-revelation-comp-min-set" type="set" value="2" field="r74-ba-r74-ba-cat-revelation-comp-min">
              <conditions>
                <condition type="atLeast" value="1" field="selections" scope="roster" childId="r25-rite-ix-0-the-day-of-revelation" shared="true" includeChildSelections="true" includeChildForces="false" />
              </conditions>
            </modifier>
            <modifier id="r75-ba-r74-ba-cat-revelation-comp-set" type="set" value="2" field="r74-ba-r74-ba-cat-revelation-comp-min">
              <conditions>
                <condition type="atLeast" value="1" field="selections" scope="roster" childId="r25-rite-ix-0-the-day-of-revelation" shared="true" includeChildSelections="true" includeChildForces="false" />
              </conditions>
            </modifier>
          </modifiers>
        </categoryLink>
        <categoryLink id="r74-ba-fl-r74-ba-cat-sorrows-comp" name="Day of Sorrows — compulsory Tactical/Assault/Breacher Troops" hidden="true" targetId="r74-ba-cat-sorrows-comp">
          <constraints>
            <constraint id="r74-ba-r74-ba-cat-sorrows-comp-min" type="min" value="0" field="selections" scope="parent" shared="true" includeChildSelections="false" includeChildForces="false" />
          </constraints>
          <modifiers>
            <modifier id="r74-ba-r74-ba-cat-sorrows-comp-min-set" type="set" value="2" field="r74-ba-r74-ba-cat-sorrows-comp-min">
              <conditions>
                <condition type="atLeast" value="1" field="selections" scope="roster" childId="r25-rite-ix-1-the-day-of-sorrows" shared="true" includeChildSelections="true" includeChildForces="false" />
              </conditions>
            </modifier>
            <modifier id="r75-ba-r74-ba-cat-sorrows-comp-set" type="set" value="2" field="r74-ba-r74-ba-cat-sorrows-comp-min">
              <conditions>
                <condition type="atLeast" value="1" field="selections" scope="roster" childId="r25-rite-ix-1-the-day-of-sorrows" shared="true" includeChildSelections="true" includeChildForces="false" />
              </conditions>
            </modifier>
          </modifiers>
        </categoryLink>
        <categoryLink id="r75-ba-fl-r75-ba-cat-rev-warlord-jump" name="Day of Revelation — Warlord with Jump Pack" hidden="true" targetId="r75-ba-cat-rev-warlord-jump">
          <constraints>
            <constraint id="r75-ba-r75-ba-cat-rev-warlord-jump-min" type="min" value="0" field="selections" scope="parent" shared="true" includeChildSelections="true" includeChildForces="false" />
          </constraints>
          <modifiers>
            <modifier id="r75-ba-r75-ba-cat-rev-warlord-jump-set" type="set" value="1" field="r75-ba-r75-ba-cat-rev-warlord-jump-min">
              <conditions>
                <condition type="atLeast" value="1" field="selections" scope="roster" childId="r25-rite-ix-0-the-day-of-revelation" shared="true" includeChildSelections="true" includeChildForces="false" />
              </conditions>
            </modifier>
          </modifiers>
        </categoryLink>
      </categoryLinks>
    </forceEntry>
  </forceEntries>
</gameSystem>