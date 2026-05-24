import { Suspense } from "react";
import Cloud from "./cloud";
import Bottom from "./bottom";
import ServerRoom from "./serverroom";
import EntranceReveal from "./EntranceReveal";

// const mapData = scMapData as CityGeoJSON,
//   outlineData = scOutlineData as CityGeoJSON;

export default function Scene() {
  return (
    <Suspense fallback={null}>
      <Cloud />

      {/* <Base data={mapData} outlineData={outlineData} /> */}

      <EntranceReveal>
        <ServerRoom />
      </EntranceReveal>

      <Bottom />
    </Suspense>
  );
}
