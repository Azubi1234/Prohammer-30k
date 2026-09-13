<?xml version='1.0' encoding='UTF-8'?>
<ns0:gameSystem xmlns:ns0="http://www.battlescribe.net/schema/gameSystemSchema" id="sys-a1d2-5ede-e74f-7479" name="Prohammer 30k" revision="9" battleScribeVersion="2.03" authorName="Prohammer 30k Project" type="gameSystem">
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
        </ns0:categoryLink>
        <ns0:categoryLink id="fl-troops" name="Troops" hidden="false" targetId="cat-troops">
          <ns0:constraints>
            <ns0:constraint id="fl-troops-min" field="selections" scope="parent" value="2" percentValue="false" shared="true" includeChildSelections="false" includeChildForces="false" type="min" />
            <ns0:constraint id="fl-troops-max" field="selections" scope="parent" value="6" percentValue="false" shared="true" includeChildSelections="false" includeChildForces="false" type="max" />
          </ns0:constraints>
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
        </ns0:categoryLink>
        <ns0:categoryLink id="fl-heavy" name="Heavy Support" hidden="false" targetId="cat-heavy">
          <ns0:constraints>
            <ns0:constraint id="fl-heavy-max" field="selections" scope="parent" value="3" percentValue="false" shared="true" includeChildSelections="false" includeChildForces="false" type="max" />
          </ns0:constraints>
        </ns0:categoryLink>
        <ns0:categoryLink id="fl-transport" name="Dedicated Transport" hidden="false" targetId="cat-transport" />
        <ns0:categoryLink id="fl-low" name="Lords of War" hidden="false" targetId="cat-low" />
        <ns0:categoryLink id="fl-aero" name="Aeronautica Imperialis" hidden="false" targetId="cat-aero">
          <ns0:constraints>
            <ns0:constraint id="fl-aero-max" field="selections" scope="parent" value="1" percentValue="false" shared="true" includeChildSelections="false" includeChildForces="false" type="max" />
          </ns0:constraints>
        </ns0:categoryLink>
      </ns0:categoryLinks>
    </ns0:forceEntry>
  </ns0:forceEntries>
</ns0:gameSystem>