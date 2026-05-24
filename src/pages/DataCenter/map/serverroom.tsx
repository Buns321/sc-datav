import { useEffect } from "react";
import { useGLTF } from "@react-three/drei";
import { MeshStandardMaterial, Color, Mesh } from "three";
import { COLORS, ROUGHNESS, METALNESS } from "./materials";

export default function ServerRoom() {
  const { scene } = useGLTF("/sc-datav/model/glb/server_room.glb");

  useEffect(() => {
    scene.traverse((child) => {
      if (!(child instanceof Mesh)) return;

      const name = child.name.toLowerCase();
      let color: string = COLORS.default;
      let roughness: number = ROUGHNESS.default;
      let metalness: number = METALNESS.default;

      if (name.startsWith("body"))       { color = COLORS.body;  roughness = ROUGHNESS.body;  metalness = METALNESS.body; }
      else if (name.startsWith("rack.")) { color = COLORS.rack;  roughness = ROUGHNESS.rack;  metalness = METALNESS.rack; }
      else if (name === "room")          { color = COLORS.floor; roughness = ROUGHNESS.floor; metalness = METALNESS.floor; }
      else if (name.startsWith("cam"))   { color = COLORS.camera; roughness = ROUGHNESS.camera; metalness = METALNESS.camera; }
      else if (name.startsWith("swbox")) { color = COLORS.swBox; roughness = ROUGHNESS.swBox; metalness = METALNESS.swBox; }
      else if (name.startsWith("sw."))   { color = COLORS.sw;    roughness = ROUGHNESS.sw;    metalness = METALNESS.sw; }
      else if (name.startsWith("firekiller")) { color = COLORS.fireKiller; roughness = ROUGHNESS.fireKiller; metalness = METALNESS.fireKiller; }

      child.material = new MeshStandardMaterial({
        color: new Color(color),
        roughness,
        metalness,
      });
    });
  }, [scene]);

  return <primitive object={scene} />;
}
