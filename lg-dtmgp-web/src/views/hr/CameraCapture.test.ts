import { flushPromises, mount } from "@vue/test-utils";
import { afterEach, describe, expect, it, vi } from "vitest";

import CameraCapture from "./CameraCapture.vue";

function setMediaDevices(value: unknown) {
  Object.defineProperty(navigator, "mediaDevices", { value, configurable: true });
}

describe("CameraCapture", () => {
  afterEach(() => setMediaDevices(undefined));

  it("explains that the camera needs HTTPS when getUserMedia is unavailable", async () => {
    setMediaDevices(undefined);
    Object.defineProperty(window, "isSecureContext", { value: false, configurable: true });
    const wrapper = mount(CameraCapture);
    await flushPromises();
    expect(wrapper.find("[role=alert]").text()).toContain("secure (HTTPS)");
    expect(wrapper.find("input[type=file]").exists()).toBe(false);
  });

  it("reports a denied camera permission and lets the user retry", async () => {
    const getUserMedia = vi.fn(() => Promise.reject(new DOMException("denied", "NotAllowedError")));
    setMediaDevices({ getUserMedia, enumerateDevices: () => Promise.resolve([]) });
    const wrapper = mount(CameraCapture);
    await flushPromises();
    expect(wrapper.find("[role=alert]").text()).toContain("Camera permission was denied");
    await wrapper.findAll("button").find((button) => button.text() === "Try again")!.trigger("click");
    expect(getUserMedia).toHaveBeenCalledTimes(2);
  });
});
