import { useGLTF } from "@react-three/drei";

export default function Model() {
    const { scene } = useGLTF("/sc-datav/model/glb/server_room.glb");
    return <primitive object={scene} />;
}
