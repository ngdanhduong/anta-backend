package vn.anta.cloud.controller;

import org.springframework.stereotype.Controller;
import org.springframework.web.bind.annotation.GetMapping;

/** Routes web browsers to the Admin and Owner static web portals with trailing-slash asset resolution. */
@Controller
public class PortalWebController {

    @GetMapping("/owner")
    public String ownerRedirect() {
        return "redirect:/owner/";
    }

    @GetMapping("/owner/")
    public String ownerHome() {
        return "forward:/owner/index.html";
    }

    @GetMapping("/admin")
    public String adminRedirect() {
        return "redirect:/admin/";
    }

    @GetMapping("/admin/")
    public String adminHome() {
        return "forward:/admin/index.html";
    }

    @GetMapping({"/portal", "/portal/"})
    public String portalHome() {
        return "forward:/index.html";
    }
}
