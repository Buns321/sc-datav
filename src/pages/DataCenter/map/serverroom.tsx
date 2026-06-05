import { useEffect } from "react";
import { useGLTF } from "@react-three/drei";
import { MeshStandardMaterial, Color, Mesh } from "three";
import { DC } from "@/config/config";

export default function ServerRoom() {
  const { scene } = useGLTF("/sc-datav/model/glb/server_room.glb");

  useEffect(() => {
    scene.traverse((child) => {
      if (!(child instanceof Mesh)) return;

      const name = child.name.toLowerCase();
      let color: string = DC.materials.default.color;
      let roughness: number = DC.materials.default.roughness;
      let metalness: number = DC.materials.default.metalness;

      if (name.startsWith("body"))       { color = DC.materials.body.color;  roughness = DC.materials.body.roughness;  metalness = DC.materials.body.metalness; }
      else if (name.startsWith("rack.")) { color = DC.materials.rack.color;  roughness = DC.materials.rack.roughness;  metalness = DC.materials.rack.metalness; }
      else if (name === "room")          { color = DC.materials.floor.color; roughness = DC.materials.floor.roughness; metalness = DC.materials.floor.metalness; }
      else if (name.startsWith("cam"))   { color = DC.materials.camera.color; roughness = DC.materials.camera.roughness; metalness = DC.materials.camera.metalness; }
      else if (name.startsWith("swbox")) { color = DC.materials.swBox.color; roughness = DC.materials.swBox.roughness; metalness = DC.materials.swBox.metalness; }
      else if (name.startsWith("sw."))   { color = DC.materials.sw.color;    roughness = DC.materials.sw.roughness;    metalness = DC.materials.sw.metalness; }
      else if (name.startsWith("firekiller")) { color = DC.materials.fireKiller.color; roughness = DC.materials.fireKiller.roughness; metalness = DC.materials.fireKiller.metalness; }

      child.material = new MeshStandardMaterial({
        color: new Color(color),
        roughness,
        metalness,
      });
    });
  }, [scene]);

  return <primitive object={scene} />;
}
