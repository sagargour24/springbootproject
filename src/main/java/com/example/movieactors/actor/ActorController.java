package com.example.movieactors.actor;

import java.util.List;

import org.springframework.web.bind.annotation.*;

@RestController
@RequestMapping(path = "api/v1/actors")
public class ActorController {
    
    private final ActorService actorService;

    public ActorController(ActorService actorService) {
        this.actorService = actorService;
    }

    @GetMapping
    public List<Actor> listActors(){
        return actorService.getActors();
    }

    @PostMapping
    public void addActor(@RequestBody Actor actor){
        actorService.addNewActor(actor);
    }

}
